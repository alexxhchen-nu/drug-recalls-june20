from pathlib import Path
import json
import os
import time
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer


QDRANT_URL = "http://localhost:6333"
DEFAULT_COLLECTION = "drug_recalls"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

# Faster CPU settings. If memory gets tight, use 64 and 500.
EMBED_BATCH_SIZE = 128
UPSERT_BATCH_SIZE = 1000

UPSERT_RETRIES = 3
UPSERT_RETRY_SLEEP_SECONDS = 5


def setup_huggingface_env() -> None:
    """
    Helps China-region servers download Hugging Face models.
    If you already exported HF_ENDPOINT manually, this will not override it.
    """
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    os.environ.setdefault("HF_HOME", "/root/.cache/huggingface")


def find_records(data: Any) -> list[dict]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]

    if isinstance(data, dict):
        for key in ["results", "records", "data", "items"]:
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]

        biggest_list: list[dict] = []

        def walk(value: Any):
            nonlocal biggest_list

            if isinstance(value, list):
                dict_items = [item for item in value if isinstance(item, dict)]

                if len(dict_items) > len(biggest_list):
                    biggest_list = dict_items

                for item in value:
                    walk(item)

            elif isinstance(value, dict):
                for child in value.values():
                    walk(child)

        walk(data)

        if biggest_list:
            return biggest_list

        return [data]

    return []


def read_json_records(input_path: Path) -> list[dict]:
    if input_path.is_file():
        json_files = [input_path]
    else:
        json_files = sorted(input_path.rglob("*.json"))

    if not json_files:
        raise FileNotFoundError(f"No .json files found in: {input_path}")

    records: list[dict] = []

    for json_file in json_files:
        if json_file.stat().st_size == 0:
            print(f"Skipping empty file: {json_file}")
            continue

        print(f"Reading: {json_file}")

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            print(f"Skipping unreadable file: {json_file}")
            print(f"Reason: {exc}")
            continue

        file_records = find_records(data)

        for record in file_records:
            record["_source_file"] = str(json_file)

        records.extend(file_records)

    return records


def extract_text(record: dict) -> str:
    preferred_fields = [
        "reason_for_recall",
        "product_description",
        "recalling_firm",
        "brand_name",
        "generic_name",
        "substance_name",
        "animal_species",
        "veddra_term_name",
        "medical_status",
        "classification",
        "status",
        "distribution_pattern",
        "description",
        "summary",
        "title",
        "text",
        "content",
    ]

    parts: list[str] = []

    for field in preferred_fields:
        value = record.get(field)
        if isinstance(value, str) and value.strip():
            parts.append(f"{field}: {value.strip()}")

    def walk(value: Any, key_name: str = ""):
        if isinstance(value, dict):
            for key, child in value.items():
                walk(child, key)
        elif isinstance(value, list):
            for item in value:
                walk(item, key_name)
        elif isinstance(value, str):
            cleaned = value.strip()
            if len(cleaned) > 2:
                label = key_name or "text"
                parts.append(f"{label}: {cleaned}")

    walk(record)

    seen = set()
    unique_parts = []

    for part in parts:
        if part not in seen:
            unique_parts.append(part)
            seen.add(part)

    return "\n".join(unique_parts)


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    text = text.strip()

    if not text:
        return []

    chunks = []
    start = 0
    step = chunk_size - overlap

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += step

    return chunks


def connect_qdrant() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL, timeout=120)


def create_collection(
    client: QdrantClient,
    collection_name: str,
    vector_size: int,
):
    collections = client.get_collections().collections
    existing_names = {collection.name for collection in collections}

    if collection_name in existing_names:
        answer = input(
            f"Collection '{collection_name}' already exists. Delete and recreate it? [y/N]: "
        ).strip().lower()

        if answer == "y":
            print(f"Deleting existing collection: {collection_name}")
            client.delete_collection(collection_name=collection_name)
        else:
            print("Keeping existing collection and appending new points.")
            return

    print(f"Creating collection: {collection_name}")

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE,
        ),
    )


def upsert_with_retry(
    client: QdrantClient,
    collection_name: str,
    points: list[PointStruct],
) -> None:
    last_error = None

    for attempt in range(1, UPSERT_RETRIES + 1):
        try:
            client.upsert(
                collection_name=collection_name,
                points=points,
                wait=True,
            )
            return
        except Exception as exc:
            last_error = exc
            print(
                f"Qdrant upsert failed on attempt {attempt}/{UPSERT_RETRIES}: {exc}"
            )

            if attempt < UPSERT_RETRIES:
                print(f"Sleeping {UPSERT_RETRY_SLEEP_SECONDS} seconds before retry...")
                time.sleep(UPSERT_RETRY_SLEEP_SECONDS)

    raise RuntimeError(f"Qdrant upsert failed after retries: {last_error}")


def flush_batch(
    client: QdrantClient,
    model: SentenceTransformer,
    collection_name: str,
    batch_chunks: list[str],
    batch_payloads: list[dict],
    start_point_id: int,
) -> int:
    if not batch_chunks:
        return start_point_id

    vectors = model.encode(
        batch_chunks,
        batch_size=EMBED_BATCH_SIZE,
        normalize_embeddings=True,
        show_progress_bar=False,
    ).tolist()

    points: list[PointStruct] = []

    for offset, vector in enumerate(vectors):
        point_id = start_point_id + offset

        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload=batch_payloads[offset],
            )
        )

    upsert_with_retry(
        client=client,
        collection_name=collection_name,
        points=points,
    )

    return start_point_id + len(points)


def ingest_json_to_qdrant():
    setup_huggingface_env()

    input_path_text = input("Enter path to JSON file or JSON directory: ").strip()
    collection_name = (
        input(f"Enter Qdrant collection name [{DEFAULT_COLLECTION}]: ").strip()
        or DEFAULT_COLLECTION
    )

    input_path = Path(input_path_text).expanduser().resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    print(f"Connecting to Qdrant at {QDRANT_URL}...")
    client = connect_qdrant()

    print(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    vector_size = model.get_sentence_embedding_dimension()

    print(f"Embedding dimension: {vector_size}")

    print("Creating Qdrant collection...")
    create_collection(
        client=client,
        collection_name=collection_name,
        vector_size=vector_size,
    )

    print("Reading JSON records...")
    records = read_json_records(input_path)

    if not records:
        raise ValueError("No readable JSON records found.")

    print(f"Found {len(records)} JSON record(s).")

    batch_chunks: list[str] = []
    batch_payloads: list[dict] = []

    next_point_id = 0
    total_chunks_seen = 0
    skipped_empty_records = 0

    started_at = time.time()

    for record_index, record in enumerate(records):
        text = extract_text(record)
        chunks = chunk_text(text)

        if not chunks:
            skipped_empty_records += 1
            continue

        for chunk_index, chunk in enumerate(chunks):
            batch_chunks.append(chunk)
            batch_payloads.append(
                {
                    "text": chunk,
                    "source_file": record.get("_source_file"),
                    "record_index": record_index,
                    "chunk_index": chunk_index,
                }
            )

            total_chunks_seen += 1

            if len(batch_chunks) >= UPSERT_BATCH_SIZE:
                before = time.time()

                next_point_id = flush_batch(
                    client=client,
                    model=model,
                    collection_name=collection_name,
                    batch_chunks=batch_chunks,
                    batch_payloads=batch_payloads,
                    start_point_id=next_point_id,
                )

                elapsed_batch = time.time() - before
                elapsed_total = time.time() - started_at

                print(
                    f"Inserted {next_point_id} chunk(s) "
                    f"| batch {len(batch_chunks)} "
                    f"| batch time {elapsed_batch:.1f}s "
                    f"| total time {elapsed_total / 60:.1f}m"
                )

                batch_chunks.clear()
                batch_payloads.clear()

    if batch_chunks:
        before = time.time()

        next_point_id = flush_batch(
            client=client,
            model=model,
            collection_name=collection_name,
            batch_chunks=batch_chunks,
            batch_payloads=batch_payloads,
            start_point_id=next_point_id,
        )

        elapsed_batch = time.time() - before
        elapsed_total = time.time() - started_at

        print(
            f"Inserted {next_point_id} chunk(s) "
            f"| final batch {len(batch_chunks)} "
            f"| batch time {elapsed_batch:.1f}s "
            f"| total time {elapsed_total / 60:.1f}m"
        )

    print()
    print("Done.")
    print(f"Collection: {collection_name}")
    print(f"Total chunks prepared: {total_chunks_seen}")
    print(f"Total chunks inserted: {next_point_id}")
    print(f"Skipped empty records: {skipped_empty_records}")
    print()
    print("Check collection:")
    print(f"curl http://localhost:6333/collections/{collection_name}")
    print()
    print("Check all collections:")
    print("curl http://localhost:6333/collections")
    print()
    print("Open dashboard through SSH tunnel:")
    print("http://localhost:6333/dashboard")


if __name__ == "__main__":
    ingest_json_to_qdrant()