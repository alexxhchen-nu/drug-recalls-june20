from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer


QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "fda2025q1"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


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


def search_qdrant():
    query = input("Ask a question: ").strip()

    limit_text = input("How many final results? [5]: ").strip()
    limit = int(limit_text) if limit_text else 5

    raw_limit = limit * 10

    client = QdrantClient(url=QDRANT_URL, timeout=120)
    model = SentenceTransformer(MODEL_NAME)

    query_vector = model.encode(
        query,
        normalize_embeddings=True,
    ).tolist()

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=raw_limit,
        with_payload=True,
    )

    seen_keys = set()
    final_results = []

    for result in response.points:
        payload = result.payload or {}
        text = payload.get("text", "")

        report_id = extract_field(text, "report_id")
        source_file = payload.get("source_file")
        record_index = payload.get("record_index")

        dedupe_key = report_id or f"{source_file}:{record_index}"

        if dedupe_key in seen_keys:
            continue

        seen_keys.add(dedupe_key)
        final_results.append(result)

        if len(final_results) >= limit:
            break

    print()
    print(f"Top {len(final_results)} de-duplicated results")
    print("=" * 80)

    for i, result in enumerate(final_results, start=1):
        payload = result.payload or {}
        text = payload.get("text", "")

        print()
        print(f"Result {i}")
        print(f"Score: {result.score:.4f}")
        print(f"Source file: {payload.get('source_file')}")
        print(f"Record index: {payload.get('record_index')}")
        print(f"Chunk index: {payload.get('chunk_index')}")
        print("-" * 80)

        print(f"Report ID: {extract_field(text, 'report_id')}")
        print(f"Species: {extract_field(text, 'species')}")
        print(f"Breed: {extract_field(text, 'breed_component')}")
        print(f"Drug/Product: {extract_field(text, 'name')}")
        print(f"Condition: {extract_field(text, 'condition')}")
        print(f"Serious AE: {extract_field(text, 'serious_ae')}")
        print(f"Medical status: {extract_field(text, 'medical_status')}")
        print(f"Info type: {extract_field(text, 'type_of_information')}")
        print()
        print("Raw text preview:")
        print(text[:1200])


if __name__ == "__main__":
    search_qdrant()