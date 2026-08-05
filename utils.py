from __future__ import annotations

import base64
import html
import mimetypes
from pathlib import Path

import streamlit as st


# ==========================================================
# PATHS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"

VALID_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".bmp",
}


# ==========================================================
# IMAGE LOOKUP
# ==========================================================

def _find_image_file(
    filename: object,
) -> Path | None:
    """
    Find an image while tolerating filename and extension differences.
    """

    if filename is None:
        return None

    cleaned_filename = str(
        filename
    ).strip()

    if not cleaned_filename:
        return None

    if not IMAGES_DIR.is_dir():
        return None

    exact_path = (
        IMAGES_DIR
        / cleaned_filename
    )

    if exact_path.is_file():
        return exact_path

    try:
        entries = list(
            IMAGES_DIR.iterdir()
        )
    except OSError:
        return None

    target_name = cleaned_filename.lower()
    target_stem = Path(
        cleaned_filename
    ).stem.lower()

    for entry in entries:
        if not entry.is_file():
            continue

        if entry.name.lower() == target_name:
            return entry

    for entry in entries:
        if not entry.is_file():
            continue

        if (
            entry.stem.lower() == target_stem
            and entry.suffix.lower() in VALID_EXTENSIONS
        ):
            return entry

    return None


def get_image_path(
    filename: object,
) -> str | None:
    """
    Return the resolved absolute path.
    """

    image_path = _find_image_file(
        filename
    )

    if image_path is None:
        return None

    return str(image_path)


# ==========================================================
# IMAGE ENCODING
# ==========================================================

@st.cache_data(show_spinner=False)
def _load_image_as_data_uri(
    path_string: str,
) -> str:
    """
    Load an image and convert it into a base64 data URI.
    """

    image_path = Path(
        path_string
    )

    mime_type, _ = mimetypes.guess_type(
        image_path.name
    )

    mime_type = (
        mime_type
        or "image/jpeg"
    )

    encoded = base64.b64encode(
        image_path.read_bytes()
    ).decode("ascii")

    return (
        f"data:{mime_type};"
        f"base64,{encoded}"
    )


# ==========================================================
# IMAGE DISPLAY
# ==========================================================

def display_image(
    image_id: object,
) -> None:
    """
    Display a hairstyle image or a safe placeholder.
    """

    path = _find_image_file(
        image_id
    )

    if path is not None:
        try:
            image_uri = _load_image_as_data_uri(
                str(path)
            )

            safe_alt = html.escape(
                path.stem
                .replace("_", " ")
                .replace("-", " ")
            )

            image_html = (
                "<img "
                "class='card-thumb' "
                f"src='{image_uri}' "
                f"alt='{safe_alt}'"
                ">"
            )

            st.markdown(
                image_html,
                unsafe_allow_html=True,
            )

            return

        except (
            OSError,
            ValueError,
        ):
            pass

    placeholder_html = (
        "<div class='card-thumb no-preview'>"
        "<div class='no-preview-icon' aria-hidden='true'>✦</div>"
        "<div class='no-preview-text'>No Preview Available</div>"
        "</div>"
    )

    st.markdown(
        placeholder_html,
        unsafe_allow_html=True,
    )


# ==========================================================
# BADGE
# ==========================================================

def badge(
    text: object,
    background: str,
    color: str,
) -> str:
    """
    Return safe badge HTML.
    """

    safe_text = html.escape(
        str(text)
    )

    return (
        "<span "
        "class='badge' "
        f"style='background:{background};color:{color};'"
        ">"
        f"{safe_text}"
        "</span>"
    )


# ==========================================================
# DIFFICULTY
# ==========================================================

def difficulty_badge(
    level: object,
) -> str:
    """
    Return a difficulty badge.
    """

    normalized = str(
        level
    ).strip().lower()

    colours = {
        "easy": (
            "#FBE7EE",
            "#A93D67",
        ),
        "beginner": (
            "#FBE7EE",
            "#A93D67",
        ),
        "intermediate": (
            "#F8EFD9",
            "#906318",
        ),
        "advanced": (
            "#F7DFE2",
            "#A43D4D",
        ),
    }

    background, foreground = colours.get(
        normalized,
        (
            "#F2EDF0",
            "#765B67",
        ),
    )

    display_text = (
        str(level).strip()
        or "Unknown"
    )

    return badge(
        display_text,
        background,
        foreground,
    )


# ==========================================================
# MATCH
# ==========================================================

def match_badge(
    score: object,
) -> str:
    """
    Return a percentage match badge.
    """

    try:
        percentage = int(
            float(score) * 100
        )
    except (
        TypeError,
        ValueError,
    ):
        percentage = 0

    percentage = max(
        0,
        min(100, percentage),
    )

    return badge(
        f"{percentage}% Match",
        "#FCE8F0",
        "#B33F6D",
    )


# ==========================================================
# CATEGORY
# ==========================================================

def category_badge(
    category: object,
) -> str:
    """
    Return a category badge.
    """

    display_text = (
        str(category).strip()
        or "General"
    )

    return badge(
        display_text,
        "#F6EBF0",
        "#7B3855",
    )


# ==========================================================
# HAIR LENGTH
# ==========================================================

def hair_badge(
    length: object,
) -> str:
    """
    Return a hair-length badge.
    """

    display_text = (
        str(length).strip()
        or "Any Length"
    )

    return badge(
        display_text,
        "#F1EDF0",
        "#684B58",
    )