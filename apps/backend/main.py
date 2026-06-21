from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer


QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "fda2025q1"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


app = FastAPI(title="FDA Animal Safety Search API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


client = QdrantClient(url=QDRANT_URL, timeout=120)
model = SentenceTransformer(MODEL_NAME)


class SearchRequest(BaseModel):
    query: str
    limit: int = 5


def extract_field(text: str, field: str) -> str:
    prefix = f"{field}: "
    values = []

    for line in text.splitlines():
        line = line.strip()
        if line.startswith(prefix):
            value = line[len(prefix):].strip()
            if value and value not in values:
                values.append(value)

    return ", ".join(values[:8])


def clean_product_name(text: str) -> str:
    name = extract_field(text, "name")
    if name:
        return name

    lines = text.splitlines()
    first_line = lines[0].strip() if lines else ""

    if first_line and ":" not in first_line and len(first_line) < 80:
        return first_line

    return "Unknown product"


def make_summary(rows: list[dict]) -> str:
    if not rows:
        return "No matching FDA animal/vet safety reports were found."

    total = len(rows)
    serious_count = sum(1 for row in rows if str(row["serious_ae"]).lower() == "true")

    species = sorted(set(row["species"] for row in rows if row["species"] != "Unknown"))
    products = sorted(set(row["drug_product"] for row in rows if row["drug_product"] != "Unknown product"))
    statuses = sorted(set(row["medical_status"] for row in rows if row["medical_status"] != "Unknown"))

    species_text = ", ".join(species[:3]) if species else "unknown species"
    product_text = ", ".join(products[:3]) if products else "unknown products"
    status_text = ", ".join(statuses[:3]) if statuses else "unknown outcomes"

    return (
        f"I found {total} relevant unique report(s). "
        f"{serious_count} report(s) were marked as serious adverse events. "
        f"The main species found: {species_text}. "
        f"The main product/drug mentions: {product_text}. "
        f"Reported medical status includes: {status_text}."
    )


@app.get("/health")
def health():
    return {"ok": True, "collection": COLLECTION_NAME}


@app.post("/search")
def search(req: SearchRequest):
    query_vector = model.encode(
        req.query,
        normalize_embeddings=True,
    ).tolist()

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=req.limit * 12,
        with_payload=True,
    )

    seen_keys = set()
    rows = []

    for result in response.points:
        payload = result.payload or {}
        text = payload.get("text", "")

        report_id = extract_field(text, "report_id") or "Unknown"
        source_file = payload.get("source_file")
        record_index = payload.get("record_index")

        dedupe_key = report_id or f"{source_file}:{record_index}"

        if dedupe_key in seen_keys:
            continue

        seen_keys.add(dedupe_key)

        rows.append(
            {
                "score": round(float(result.score), 4),
                "report_id": report_id,
                "species": extract_field(text, "species") or "Unknown",
                "breed": extract_field(text, "breed_component") or "Unknown",
                "drug_product": clean_product_name(text),
                "condition": extract_field(text, "condition") or "Unknown",
                "serious_ae": extract_field(text, "serious_ae") or "Unknown",
                "medical_status": extract_field(text, "medical_status") or "Unknown",
                "info_type": extract_field(text, "type_of_information") or "Unknown",
                "source_file": source_file,
                "record_index": record_index,
                "chunk_index": payload.get("chunk_index"),
                "raw_text": text[:5000],
            }
        )

        if len(rows) >= req.limit:
            break

    return {
        "query": req.query,
        "summary": make_summary(rows),
        "count": len(rows),
        "results": rows,
    }
