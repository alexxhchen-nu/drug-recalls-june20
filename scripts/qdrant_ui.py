import pandas as pd
import streamlit as st
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer


QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "fda2025q1"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


st.set_page_config(
    page_title="FDA Animal Safety Search",
    page_icon="🐾",
    layout="wide",
)


CUSTOM_CSS = """
<style>
    .stApp {
        background: linear-gradient(180deg, #fafafa 0%, #f4f4f5 100%);
    }

    .main-title {
        font-size: 48px;
        font-weight: 800;
        letter-spacing: -1.5px;
        color: #18181b;
        margin-bottom: 4px;
    }

    .subtitle {
        color: #71717a;
        font-size: 18px;
        margin-bottom: 28px;
    }

    .hero-card {
        background: white;
        border: 1px solid #e4e4e7;
        border-radius: 28px;
        padding: 28px;
        box-shadow: 0 18px 45px rgba(15, 23, 42, 0.06);
        margin-bottom: 24px;
    }

    .answer-card {
        background: #18181b;
        color: white;
        border-radius: 28px;
        padding: 26px 30px;
        margin: 24px 0;
        box-shadow: 0 20px 50px rgba(24, 24, 27, 0.16);
    }

    .answer-card h3 {
        color: white;
        margin-top: 0;
        font-size: 22px;
    }

    .answer-card p {
        color: #e4e4e7;
        font-size: 17px;
        line-height: 1.6;
    }

    .metric-card {
        background: white;
        border: 1px solid #e4e4e7;
        border-radius: 22px;
        padding: 20px;
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.04);
    }

    .result-card {
        background: white;
        border: 1px solid #e4e4e7;
        border-radius: 24px;
        padding: 22px;
        margin-bottom: 18px;
        box-shadow: 0 14px 35px rgba(15, 23, 42, 0.05);
    }

    .badge {
        display: inline-block;
        padding: 6px 11px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 700;
        margin-right: 6px;
        margin-bottom: 6px;
    }

    .badge-neutral {
        background: #f4f4f5;
        color: #3f3f46;
    }

    .badge-red {
        background: #fee2e2;
        color: #991b1b;
    }

    .badge-green {
        background: #dcfce7;
        color: #166534;
    }

    .badge-blue {
        background: #dbeafe;
        color: #1e40af;
    }

    .small-muted {
        color: #71717a;
        font-size: 14px;
    }

    div[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e4e4e7;
    }

    .stButton > button {
        border-radius: 999px;
        padding: 0.65rem 1.4rem;
        font-weight: 700;
    }

    .stTextInput > div > div > input {
        border-radius: 18px;
        padding: 18px;
        font-size: 17px;
    }

    .stSelectbox > div > div {
        border-radius: 16px;
    }
</style>
"""


st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_resource
def get_model():
    return SentenceTransformer(MODEL_NAME)


@st.cache_resource
def get_client():
    return QdrantClient(url=QDRANT_URL, timeout=120)


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

    first_line = text.splitlines()[0].strip() if text.splitlines() else ""
    if first_line and ":" not in first_line and len(first_line) < 80:
        return first_line

    return "Unknown product"


def search_qdrant(query: str, limit: int = 5):
    client = get_client()
    model = get_model()

    query_vector = model.encode(
        query,
        normalize_embeddings=True,
    ).tolist()

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit * 12,
        with_payload=True,
    )

    seen_keys = set()
    rows = []

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

        rows.append(
            {
                "score": round(float(result.score), 4),
                "report_id": report_id or "Unknown",
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
                "raw_text": text,
            }
        )

        if len(rows) >= limit:
            break

    return rows


def make_summary(rows):
    if not rows:
        return "No matching records were found."

    total = len(rows)
    serious_count = sum(1 for r in rows if str(r["serious_ae"]).lower() == "true")

    species = sorted(set(r["species"] for r in rows if r["species"] != "Unknown"))
    products = sorted(set(r["drug_product"] for r in rows if r["drug_product"] != "Unknown product"))
    statuses = sorted(set(r["medical_status"] for r in rows if r["medical_status"] != "Unknown"))

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


def serious_badge(value: str) -> str:
    if str(value).lower() == "true":
        return '<span class="badge badge-red">Serious AE</span>'
    if str(value).lower() == "false":
        return '<span class="badge badge-green">Non-serious</span>'
    return '<span class="badge badge-neutral">Seriousness unknown</span>'


def status_badge(value: str) -> str:
    return f'<span class="badge badge-blue">{value}</span>'


with st.sidebar:
    st.markdown("## 🐾 Search Settings")
    limit = st.slider("How many results?", min_value=1, max_value=20, value=5)

    st.markdown("### Quick examples")
    example = st.selectbox(
        "Choose an example",
        [
            "bexagliflozin cat serious adverse event",
            "dog vomiting adverse event",
            "death reported serious adverse event dog",
            "cat outcome unknown medication",
            "lack of expected effectiveness cat",
            "application site irritation dog",
        ],
    )

    st.markdown("### Data source")
    st.code(COLLECTION_NAME)

    st.markdown(
        """
        <div class="small-muted">
        This app searches FDA animal/vet safety records using semantic search.
        Results are evidence records, not medical advice.
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown('<div class="main-title">FDA Animal Safety Search</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Ask plain-English questions about animal drug safety reports.</div>',
    unsafe_allow_html=True,
)

st.markdown('<div class="hero-card">', unsafe_allow_html=True)

query = st.text_input(
    "What do you want to find?",
    value=example,
    placeholder="Example: cats with serious adverse events after Bexagliflozin",
)

col_a, col_b = st.columns([1, 5])

with col_a:
    search_clicked = st.button("Search", type="primary")

with col_b:
    st.caption("Try asking about a species, product, symptom, seriousness, or outcome.")

st.markdown("</div>", unsafe_allow_html=True)


if search_clicked and query.strip():
    with st.spinner("Searching FDA records..."):
        rows = search_qdrant(query.strip(), limit=limit)

    if not rows:
        st.warning("No matching records found. Try a broader search, such as the species and product name.")
    else:
        summary = make_summary(rows)

        st.markdown(
            f"""
            <div class="answer-card">
                <h3>Plain-English summary</h3>
                <p>{summary}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        m1, m2, m3, m4 = st.columns(4)

        serious_count = sum(1 for r in rows if str(r["serious_ae"]).lower() == "true")
        unique_species = len(set(r["species"] for r in rows))
        unique_products = len(set(r["drug_product"] for r in rows))
        avg_score = sum(r["score"] for r in rows) / len(rows)

        m1.metric("Unique reports", len(rows))
        m2.metric("Serious AE", serious_count)
        m3.metric("Species found", unique_species)
        m4.metric("Avg match score", round(avg_score, 3))

        st.markdown("## Results")

        display_rows = [
            {
                "Match": r["score"],
                "Report ID": r["report_id"],
                "Species": r["species"],
                "Product": r["drug_product"],
                "Serious AE": r["serious_ae"],
                "Medical Status": r["medical_status"],
                "Info Type": r["info_type"],
            }
            for r in rows
        ]

        df = pd.DataFrame(display_rows)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download results as CSV",
            data=csv,
            file_name="fda_animal_safety_search_results.csv",
            mime="text/csv",
        )

        st.markdown("## Evidence cards")

        for i, row in enumerate(rows, start=1):
            st.markdown(
                f"""
                <div class="result-card">
                    <h3>{i}. {row["drug_product"]}</h3>
                    <div>
                        <span class="badge badge-neutral">Report {row["report_id"]}</span>
                        <span class="badge badge-neutral">{row["species"]}</span>
                        <span class="badge badge-neutral">{row["breed"]}</span>
                        {serious_badge(row["serious_ae"])}
                        {status_badge(row["medical_status"])}
                    </div>
                    <p class="small-muted">
                        Match score: {row["score"]} · Info type: {row["info_type"]}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.expander("View full evidence"):
                key_df = pd.DataFrame(
                    [
                        ["Report ID", row["report_id"]],
                        ["Product / Drug", row["drug_product"]],
                        ["Species", row["species"]],
                        ["Breed", row["breed"]],
                        ["Condition", row["condition"]],
                        ["Serious AE", row["serious_ae"]],
                        ["Medical Status", row["medical_status"]],
                        ["Info Type", row["info_type"]],
                        ["Source File", row["source_file"]],
                        ["Record Index", row["record_index"]],
                        ["Chunk Index", row["chunk_index"]],
                    ],
                    columns=["Field", "Value"],
                )

                st.table(key_df)
                st.markdown("#### Raw evidence text")
                st.code(row["raw_text"][:4000])
else:
    st.info("Enter a question and click Search.")