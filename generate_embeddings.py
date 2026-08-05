from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer


# ==========================================================
# PATHS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH = (
    BASE_DIR
    / "data"
    / "annist_dataset.csv"
)

EMBEDDINGS_DIR = (
    BASE_DIR
    / "embeddings"
)

EMBEDDINGS_PATH = (
    EMBEDDINGS_DIR
    / "annist_embeddings.npy"
)

MODEL_NAME = "BAAI/bge-small-en-v1.5"


# ==========================================================
# DATASET REQUIREMENTS
# ==========================================================

REQUIRED_COLUMNS = {
    "hairstyle_label",
    "category",
    "difficulty",
    "hair_length",
    "description",
    "keywords",
    "search_profile",
}


def validate_dataset(
    dataframe: pd.DataFrame,
) -> None:
    """
    Confirm that the ANNIST dataset contains all fields needed to
    generate searchable embeddings.
    """

    missing_columns = REQUIRED_COLUMNS.difference(
        dataframe.columns
    )

    if missing_columns:
        missing_text = ", ".join(
            sorted(missing_columns)
        )

        raise ValueError(
            "The ANNIST dataset is missing these required columns: "
            f"{missing_text}"
        )


# ==========================================================
# SEARCHABLE TEXT
# ==========================================================

def safe_text(value: object) -> str:
    """
    Convert a dataset value into clean text.
    """

    if pd.isna(value):
        return ""

    return str(value).strip()


def build_search_text(
    row: pd.Series,
) -> str:
    """
    Build one searchable text document for a hairstyle row.
    """

    parts = [
        safe_text(row["hairstyle_label"]),
        safe_text(row["category"]),
        safe_text(row["difficulty"]),
        safe_text(row["hair_length"]),
        safe_text(row["description"]),
        safe_text(row["keywords"]),
        safe_text(row["search_profile"]),
    ]

    return " ".join(
        part
        for part in parts
        if part
    )


# ==========================================================
# MAIN GENERATION
# ==========================================================

def generate_embeddings() -> None:
    """
    Load the dataset, generate normalized embeddings, and save them.
    """

    if not DATASET_PATH.is_file():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    EMBEDDINGS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print("=" * 60)
    print("ANNIST Embedding Generator")
    print("=" * 60)
    print()

    print(
        f"Loading dataset from:\n{DATASET_PATH}"
    )

    dataframe = pd.read_csv(
        DATASET_PATH
    )

    validate_dataset(
        dataframe
    )

    if dataframe.empty:
        raise ValueError(
            "The ANNIST dataset is empty."
        )

    print(
        f"Loaded {len(dataframe)} hairstyles."
    )

    print()
    print("Building searchable text...")

    search_documents = [
        build_search_text(row)
        for _, row in dataframe.iterrows()
    ]

    print(
        f"Built {len(search_documents)} search documents."
    )

    print()
    print(
        f"Loading embedding model: {MODEL_NAME}"
    )

    model = SentenceTransformer(
        MODEL_NAME
    )

    print()
    print("Generating embeddings...")

    embeddings = model.encode(
        search_documents,
        batch_size=32,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    embeddings = np.asarray(
        embeddings,
        dtype=np.float32,
    )

    if embeddings.ndim != 2:
        raise ValueError(
            "The model returned embeddings with an invalid shape."
        )

    if len(embeddings) != len(dataframe):
        raise ValueError(
            "The number of generated embeddings does not match "
            "the number of dataset rows."
        )

    np.save(
        EMBEDDINGS_PATH,
        embeddings,
        allow_pickle=False,
    )

    print()
    print("Embedding generation complete.")
    print(
        f"Embedding shape: {embeddings.shape}"
    )
    print(
        f"Saved to:\n{EMBEDDINGS_PATH}"
    )
    print()


# ==========================================================
# SCRIPT ENTRY POINT
# ==========================================================

if __name__ == "__main__":
    generate_embeddings()