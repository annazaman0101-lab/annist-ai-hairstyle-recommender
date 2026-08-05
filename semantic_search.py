from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st
from sentence_transformers import SentenceTransformer


# ==========================================================
# PATHS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "data" / "annist_dataset.csv"
EMBEDDINGS_PATH = BASE_DIR / "embeddings" / "annist_embeddings.npy"

MODEL_NAME = "BAAI/bge-small-en-v1.5"


# ==========================================================
# VALIDATION
# ==========================================================

REQUIRED_COLUMNS = {
    "filename",
    "hairstyle_label",
    "category",
    "difficulty",
    "hair_length",
    "description",
    "keywords",
    "search_profile",
}


def _validate_dataset(dataframe: pd.DataFrame) -> None:
    """
    Ensure the dataset includes every column required by ANNIST.
    """

    missing_columns = REQUIRED_COLUMNS.difference(dataframe.columns)

    if missing_columns:
        missing_text = ", ".join(sorted(missing_columns))

        raise ValueError(
            "ANNIST dataset is missing required columns: "
            f"{missing_text}"
        )


# ==========================================================
# LOAD DATA
# ==========================================================

@st.cache_data(show_spinner=False)
def _load_dataset() -> pd.DataFrame:
    """
    Load and preprocess the hairstyle dataset.
    """

    if not DATASET_PATH.is_file():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    dataframe = pd.read_csv(DATASET_PATH)

    _validate_dataset(dataframe)

    dataframe = dataframe.copy()

    dataframe["_occasion_tags"] = dataframe["category"].apply(
        _split_tags
    )

    dataframe["_hair_length_tags"] = dataframe["hair_length"].apply(
        _split_tags
    )

    dataframe["_difficulty_norm"] = dataframe["difficulty"].apply(
        _normalize_difficulty
    )

    return dataframe


@st.cache_resource(show_spinner=False)
def _load_model() -> SentenceTransformer:
    """
    Load the sentence-transformer model once per Streamlit process.
    """

    return SentenceTransformer(MODEL_NAME)


@st.cache_data(show_spinner=False)
def _load_embeddings() -> np.ndarray:
    """
    Load pre-generated hairstyle embeddings.
    """

    if not EMBEDDINGS_PATH.is_file():
        raise FileNotFoundError(
            "ANNIST embeddings were not found at "
            f"{EMBEDDINGS_PATH}. Run generate_embeddings.py first."
        )

    embeddings = np.load(
        EMBEDDINGS_PATH,
        allow_pickle=False,
    )

    if embeddings.ndim != 2:
        raise ValueError(
            "ANNIST embeddings must be a two-dimensional NumPy array."
        )

    return embeddings


# ==========================================================
# NORMALIZATION
# ==========================================================

def _split_tags(value: Any) -> list[str]:
    """
    Split slash-separated dataset values into normalized tags.
    """

    if pd.isna(value):
        return []

    return [
        tag.strip().lower()
        for tag in str(value).split("/")
        if tag.strip()
    ]


def _normalize_difficulty(value: Any) -> str:
    """
    Normalize difficulty values.

    The interface uses Easy, while some datasets use Beginner.
    Both values are treated as the same skill level.
    """

    normalized = str(value).strip().lower()

    aliases = {
        "easy": "beginner",
        "beginner": "beginner",
        "intermediate": "intermediate",
        "advanced": "advanced",
    }

    return aliases.get(
        normalized,
        normalized,
    )


# ==========================================================
# ORDERED SCALES
# ==========================================================

SKILL_SCALE = [
    "beginner",
    "intermediate",
    "advanced",
]

LENGTH_SCALE = [
    "short",
    "medium",
    "long",
]


def _scale_distance(
    value: str,
    target: str,
    scale: list[str],
) -> int | None:
    """
    Return the distance between two values on an ordered scale.
    """

    if value not in scale or target not in scale:
        return None

    return abs(
        scale.index(value) - scale.index(target)
    )


# ==========================================================
# QUERY EXPANSION
# ==========================================================

QUERY_EXPANSIONS = {
    "university": [
        "college",
        "student",
        "campus",
        "everyday",
        "simple",
        "casual",
        "quick",
    ],
    "college": [
        "student",
        "campus",
        "everyday",
        "simple",
        "casual",
    ],
    "school": [
        "student",
        "simple",
        "everyday",
        "quick",
    ],
    "interview": [
        "professional",
        "office",
        "business",
        "formal",
        "sleek",
        "clean",
        "neat",
        "low bun",
        "ponytail",
    ],
    "office": [
        "professional",
        "business",
        "formal",
        "clean",
        "sleek",
    ],
    "work": [
        "office",
        "business",
        "professional",
    ],
    "gym": [
        "workout",
        "sport",
        "secure",
        "tight",
        "ponytail",
        "braid",
        "comfortable",
    ],
    "workout": [
        "gym",
        "sport",
        "secure",
        "tight",
        "ponytail",
        "braid",
    ],
    "wedding": [
        "bridal",
        "nikah",
        "walima",
        "reception",
        "elegant",
        "formal",
    ],
    "bridal": [
        "wedding",
        "nikah",
        "walima",
        "reception",
        "elegant",
    ],
    "party": [
        "birthday",
        "celebration",
        "glam",
        "cute",
        "trendy",
    ],
    "everyday": [
        "daily",
        "casual",
        "simple",
        "comfortable",
        "quick",
    ],
    "easy": [
        "simple",
        "quick",
        "beginner",
        "fast",
    ],
    "beginner": [
        "easy",
        "simple",
        "quick",
    ],
}


def expand_query(query: str) -> str:
    """
    Enrich a user query with semantically related hairstyle terms.
    """

    normalized_query = query.strip().lower()

    if not normalized_query:
        return ""

    additions: list[str] = []

    for trigger, related_terms in QUERY_EXPANSIONS.items():
        if trigger in normalized_query:
            additions.extend(related_terms)

    if not additions:
        return normalized_query

    unique_additions = list(
        dict.fromkeys(additions)
    )

    return (
        normalized_query
        + " "
        + " ".join(unique_additions)
    )


# ==========================================================
# FILTERING
# ==========================================================

def _apply_filters(
    dataframe: pd.DataFrame,
    category: str,
    difficulty: str,
    hair_length: str,
    skill_mode: str = "exact",
    length_mode: str = "exact",
    occasion_mode: str = "exact",
) -> pd.DataFrame:
    """
    Apply categorical filters using exact, adjacent, or any modes.
    """

    mask = pd.Series(
        True,
        index=dataframe.index,
        dtype=bool,
    )

    # ------------------------------------------------------
    # Occasion
    # ------------------------------------------------------

    if category != "All":
        target_category = category.strip().lower()

        if occasion_mode == "exact":
            mask &= dataframe["_occasion_tags"].apply(
                lambda tags: target_category in tags
            )

        elif occasion_mode == "adjacent":
            mask &= dataframe["_occasion_tags"].apply(
                lambda tags: (
                    target_category in tags
                    or "everyday" in tags
                    or "simple" in tags
                )
            )

        elif occasion_mode != "any":
            raise ValueError(
                f"Unsupported occasion mode: {occasion_mode}"
            )

    # ------------------------------------------------------
    # Hair length
    # ------------------------------------------------------

    if hair_length != "All":
        target_length = hair_length.strip().lower()

        if length_mode == "exact":
            mask &= dataframe["_hair_length_tags"].apply(
                lambda tags: target_length in tags
            )

        elif length_mode == "adjacent":

            def length_matches(tags: list[str]) -> bool:
                for tag in tags:
                    distance = _scale_distance(
                        tag,
                        target_length,
                        LENGTH_SCALE,
                    )

                    if (
                        distance is not None
                        and distance <= 1
                    ):
                        return True

                return False

            mask &= dataframe["_hair_length_tags"].apply(
                length_matches
            )

        elif length_mode != "any":
            raise ValueError(
                f"Unsupported hair-length mode: {length_mode}"
            )

    # ------------------------------------------------------
    # Difficulty
    # ------------------------------------------------------

    if difficulty != "All":
        target_skill = _normalize_difficulty(
            difficulty
        )

        if skill_mode == "exact":
            mask &= (
                dataframe["_difficulty_norm"]
                == target_skill
            )

        elif skill_mode == "adjacent":

            def skill_matches(value: str) -> bool:
                distance = _scale_distance(
                    value,
                    target_skill,
                    SKILL_SCALE,
                )

                return (
                    distance is not None
                    and distance <= 1
                )

            mask &= dataframe["_difficulty_norm"].apply(
                skill_matches
            )

        elif skill_mode != "any":
            raise ValueError(
                f"Unsupported skill mode: {skill_mode}"
            )

    return dataframe.loc[mask].copy()


# ==========================================================
# MATCH CREDIT
# ==========================================================

def _credit(
    mode: str,
    exact_match: bool,
    relaxed_match: bool,
) -> float:
    """
    Return match credit for one filter dimension.
    """

    if exact_match:
        return 1.0

    if mode == "adjacent" and relaxed_match:
        return 0.55

    if mode == "any":
        return 0.55

    return 0.15


def _dimension_credit(
    row: pd.Series,
    category: str,
    difficulty: str,
    hair_length: str,
    skill_mode: str,
    length_mode: str,
    occasion_mode: str,
) -> tuple[float, float, float]:
    """
    Calculate occasion, length, and skill match credits.
    """

    # ------------------------------------------------------
    # Occasion credit
    # ------------------------------------------------------

    if category == "All":
        occasion_credit = 1.0

    else:
        target_category = category.strip().lower()
        occasion_tags = row["_occasion_tags"]

        exact_occasion = (
            target_category in occasion_tags
        )

        relaxed_occasion = (
            "everyday" in occasion_tags
            or "simple" in occasion_tags
        )

        occasion_credit = _credit(
            occasion_mode,
            exact_occasion,
            relaxed_occasion,
        )

    # ------------------------------------------------------
    # Hair-length credit
    # ------------------------------------------------------

    if hair_length == "All":
        length_credit = 1.0

    else:
        target_length = hair_length.strip().lower()
        length_tags = row["_hair_length_tags"]

        exact_length = (
            target_length in length_tags
        )

        relaxed_length = any(
            (
                distance is not None
                and distance <= 1
            )
            for distance in (
                _scale_distance(
                    tag,
                    target_length,
                    LENGTH_SCALE,
                )
                for tag in length_tags
            )
        )

        length_credit = _credit(
            length_mode,
            exact_length,
            relaxed_length,
        )

    # ------------------------------------------------------
    # Difficulty credit
    # ------------------------------------------------------

    if difficulty == "All":
        skill_credit = 1.0

    else:
        target_skill = _normalize_difficulty(
            difficulty
        )

        row_skill = row["_difficulty_norm"]

        exact_skill = (
            row_skill == target_skill
        )

        skill_distance = _scale_distance(
            row_skill,
            target_skill,
            SKILL_SCALE,
        )

        relaxed_skill = (
            skill_distance is not None
            and skill_distance <= 1
        )

        skill_credit = _credit(
            skill_mode,
            exact_skill,
            relaxed_skill,
        )

    return (
        occasion_credit,
        length_credit,
        skill_credit,
    )


# ==========================================================
# RANKING
# ==========================================================

def _rank_subset(
    subset: pd.DataFrame,
    embeddings: np.ndarray,
    model: SentenceTransformer,
    query: str,
    category: str,
    difficulty: str,
    hair_length: str,
    skill_mode: str,
    length_mode: str,
    occasion_mode: str,
    top_k: int,
) -> pd.DataFrame:
    """
    Rank a filtered dataset subset using semantic and categorical scores.
    """

    if subset.empty:
        return subset

    ranked_subset = subset.copy()

    clean_query = (query or "").strip()

    # ------------------------------------------------------
    # Semantic score
    # ------------------------------------------------------

    if clean_query:
        expanded_query = expand_query(
            clean_query
        )

        query_embedding = model.encode(
            expanded_query,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        row_indexes = ranked_subset.index.to_numpy()

        if row_indexes.max(initial=-1) >= len(embeddings):
            raise ValueError(
                "The embeddings file does not match the dataset. "
                "Run generate_embeddings.py again."
            )

        subset_embeddings = embeddings[row_indexes]

        semantic_scores = np.dot(
            subset_embeddings,
            query_embedding,
        )

        semantic_scores = np.clip(
            semantic_scores,
            0.0,
            1.0,
        )

    else:
        semantic_scores = np.ones(
            len(ranked_subset),
            dtype=np.float32,
        )

    ranked_subset["semantic_score"] = semantic_scores

    # ------------------------------------------------------
    # Filter credits
    # ------------------------------------------------------

    occasion_credits: list[float] = []
    length_credits: list[float] = []
    skill_credits: list[float] = []

    for _, row in ranked_subset.iterrows():
        (
            occasion_credit,
            length_credit,
            skill_credit,
        ) = _dimension_credit(
            row=row,
            category=category,
            difficulty=difficulty,
            hair_length=hair_length,
            skill_mode=skill_mode,
            length_mode=length_mode,
            occasion_mode=occasion_mode,
        )

        occasion_credits.append(
            occasion_credit
        )

        length_credits.append(
            length_credit
        )

        skill_credits.append(
            skill_credit
        )

    ranked_subset["_occasion_credit"] = occasion_credits
    ranked_subset["_length_credit"] = length_credits
    ranked_subset["_skill_credit"] = skill_credits

    # ------------------------------------------------------
    # Weighted AI match score
    # ------------------------------------------------------

    ranked_subset["score"] = (
        ranked_subset["semantic_score"] * 0.40
        + ranked_subset["_occasion_credit"] * 0.30
        + ranked_subset["_length_credit"] * 0.20
        + ranked_subset["_skill_credit"] * 0.10
    )

    ranked_subset = (
        ranked_subset
        .sort_values(
            by="score",
            ascending=False,
        )
        .drop_duplicates(
            subset="hairstyle_label",
        )
        .head(top_k)
        .reset_index(drop=True)
    )

    return ranked_subset


# ==========================================================
# RELAXATION LADDER
# ==========================================================

RELAXATION_LADDER = [
    (
        "exact",
        "exact",
        "exact",
        None,
    ),
    (
        "adjacent",
        "exact",
        "exact",
        "No exact hairstyle was found. Showing the closest matches.",
    ),
    (
        "adjacent",
        "adjacent",
        "exact",
        "No exact hairstyle was found. Showing the closest matches.",
    ),
    (
        "adjacent",
        "adjacent",
        "adjacent",
        "No exact hairstyle was found. Showing the closest matches.",
    ),
    (
        "any",
        "any",
        "any",
        "No exact hairstyle was found. Showing the closest matches.",
    ),
]


# ==========================================================
# PUBLIC SEARCH FUNCTION
# ==========================================================

def search_hairstyles(
    query: str,
    category: str = "All",
    difficulty: str = "All",
    hair_length: str = "All",
    top_k: int = 9,
) -> tuple[pd.DataFrame, str | None]:
    """
    Search and rank hairstyle recommendations.

    The search process is:

    1. Apply strict categorical filters.
    2. Progressively relax filters only when no exact rows exist.
    3. Use semantic similarity to rerank the filtered subset.
    4. Return up to top_k recommendations.
    """

    dataframe = _load_dataset()
    embeddings = _load_embeddings()
    model = _load_model()

    if len(dataframe) != len(embeddings):
        raise ValueError(
            "The number of dataset rows does not match the number "
            "of saved embeddings. Run generate_embeddings.py again."
        )

    safe_top_k = max(
        1,
        int(top_k),
    )

    for (
        skill_mode,
        length_mode,
        occasion_mode,
        fallback_message,
    ) in RELAXATION_LADDER:

        subset = _apply_filters(
            dataframe=dataframe,
            category=category,
            difficulty=difficulty,
            hair_length=hair_length,
            skill_mode=skill_mode,
            length_mode=length_mode,
            occasion_mode=occasion_mode,
        )

        if subset.empty:
            continue

        ranked_results = _rank_subset(
            subset=subset,
            embeddings=embeddings,
            model=model,
            query=query,
            category=category,
            difficulty=difficulty,
            hair_length=hair_length,
            skill_mode=skill_mode,
            length_mode=length_mode,
            occasion_mode=occasion_mode,
            top_k=safe_top_k,
        )

        return (
            ranked_results,
            fallback_message,
        )

    return (
        dataframe.head(0).copy(),
        "No matching hairstyles found.",
    )


# ==========================================================
# TERMINAL TESTING
# ==========================================================

if __name__ == "__main__":
    print()
    print("=" * 60)
    print("ANNIST AI Hairstyle Search")
    print("=" * 60)
    print("Type 'exit' to quit.")
    print()

    while True:
        user_query = input(
            "Ask ANNIST: "
        ).strip()

        if user_query.lower() == "exit":
            print()
            print("Thanks for using ANNIST!")
            break

        results, message = search_hairstyles(
            query=user_query,
        )

        if message:
            print()
            print(message)

        print()
        print("Top Recommendations")
        print()

        for position, (_, row) in enumerate(
            results.iterrows(),
            start=1,
        ):
            print(
                f"{position}. "
                f"{row['hairstyle_label']}"
            )

            print(
                "   Category    : "
                f"{row['category']}"
            )

            print(
                "   Difficulty  : "
                f"{row['difficulty']}"
            )

            print(
                "   Hair Length : "
                f"{row['hair_length']}"
            )

            print(
                "   Match Score : "
                f"{row['score']:.3f}"
            )

            if "description" in row.index:
                print(
                    "   Description : "
                    f"{row['description']}"
                )

            print("-" * 60)