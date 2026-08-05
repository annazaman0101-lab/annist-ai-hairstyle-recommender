"""
app.py — ANNIST entry point.

Run with:  streamlit run app.py

Structure
    page config  ->  styles  ->  session state  ->  router
    router dispatches to render_home() or render_details()

The only code that talks to your semantic search engine lives in the
"SEARCH INTEGRATION" section. Nothing else in this file knows how ranking
works, and semantic_search.py is never modified.
"""

import os
from typing import Any, Dict, List, Optional

import streamlit as st

# st.set_page_config must be the first Streamlit call in the whole app, and it
# must never be called from another module.
st.set_page_config(
    page_title="ANNIST — Your Perfect Hairstyle",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

import components as ui  # noqa: E402  (import after set_page_config, by design)

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STYLES_PATH = os.path.join(BASE_DIR, "styles.css")
def first_existing(*candidates: str) -> str:
    """Return the first path that exists, else the first candidate."""
    for path in candidates:
        if os.path.isfile(path):
            return path
    return candidates[0]


ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Brand art is inlined as a base64 data URI so it can be styled as part of the
# layout. That payload crosses the websocket on every rerun, so these files are
# kept small — WebP first, PNG only as a fallback.
LOGO_PATH = first_existing(
    os.path.join(ASSETS_DIR, "logo.webp"),
    os.path.join(ASSETS_DIR, "logo.png"),
)
HERO_PATH = first_existing(
    os.path.join(ASSETS_DIR, "hero_illustration.webp"),
    os.path.join(ASSETS_DIR, "hero_illustration.png"),
)

# Folders searched, in order, when a dataset row gives a bare image filename.
IMAGE_DIRS = [
    os.path.join(BASE_DIR, "images"),
    os.path.join(BASE_DIR, "assets", "images"),
    os.path.join(BASE_DIR, "assets"),
    BASE_DIR,
]

TOP_K = 9

# ===========================================================================
# SEARCH INTEGRATION
# ---------------------------------------------------------------------------
# semantic_search.py exposes one public entry point:
#
#     search_hairstyles(query, category, difficulty, hair_length, top_k)
#         -> (DataFrame, fallback_message | None)
#
# It uses the string "All" rather than None to mean "no filter", and it runs
# its own relaxation ladder, so the UI passes the raw query through unchanged
# and lets the engine own all ranking.
# ===========================================================================

ALL = "All"

try:
    import semantic_search

    ENGINE_IMPORT_ERROR: Optional[BaseException] = None
except Exception as exc:  # missing deps, bad paths, import-time failures
    semantic_search = None  # type: ignore[assignment]
    ENGINE_IMPORT_ERROR = exc


# ---------------------------------------------------------------------------
# FILTER OPTIONS
# Read from the dataset itself so the dropdowns always match the data, and
# the labels shown in the cards match the labels in the filters.
# ---------------------------------------------------------------------------

FALLBACK_OPTIONS = {
    "occasion": ["Wedding", "Party", "Work", "University", "Everyday"],
    "hair_length": ["Short", "Medium", "Long"],
    "skill": ["Easy", "Intermediate", "Advanced"],
}


def split_tags(value: Any) -> List[str]:
    """Dataset columns pack several tags into one slash-separated cell."""
    if value is None:
        return []
    text = str(value)
    if text.strip().lower() in ("", "nan"):
        return []
    return [part.strip() for part in text.split("/") if part.strip()]


def titled(tag: str) -> str:
    """Title-case a tag without mangling ones the dataset already capitalised."""
    return tag if any(c.isupper() for c in tag) else tag.title()


def unique_tags(series: Any) -> List[str]:
    """Distinct tags across a column, keeping the dataset's own casing."""
    found: List[str] = []
    seen = set()
    for value in series:
        for tag in split_tags(value):
            key = tag.lower()
            if key not in seen:
                seen.add(key)
                found.append(tag)
    return found


def scale_key(value: str, scale: List[str]) -> int:
    """Sort position for an ordered scale; unknown values sort last."""
    normalised = str(value).strip().lower()
    if scale is semantic_search.SKILL_SCALE:
        normalised = semantic_search._normalize_difficulty(normalised)
    return scale.index(normalised) if normalised in scale else len(scale)


def ordered(values: List[str], scale: Optional[List[str]]) -> List[str]:
    if scale is None:
        return sorted(values, key=str.lower)
    return sorted(values, key=lambda v: (scale_key(v, scale), v.lower()))


@st.cache_data(show_spinner=False)
def filter_options() -> Dict[str, List[str]]:
    """Dropdown choices, derived from the ANNIST dataset."""
    if semantic_search is None:
        return dict(FALLBACK_OPTIONS)
    try:
        frame = semantic_search._load_dataset()
    except Exception:
        return dict(FALLBACK_OPTIONS)

    # Labels are title-cased for display; _apply_filters lowercases them again,
    # so the values still match the dataset tags exactly.
    return {
        "occasion": ordered(
            [titled(t) for t in unique_tags(frame["category"])], None
        ),
        "hair_length": ordered(
            [titled(t) for t in unique_tags(frame["hair_length"])],
            semantic_search.LENGTH_SCALE,
        ),
        "skill": ordered(
            [titled(t) for t in unique_tags(frame["difficulty"])],
            semantic_search.SKILL_SCALE,
        ),
    }


# ---------------------------------------------------------------------------
# RESULT NORMALISATION
# Maps the ANNIST dataset columns onto the keys the UI components read.
# ---------------------------------------------------------------------------

IMAGE_DIRS = [
    os.path.join(BASE_DIR, "images"),
    os.path.join(BASE_DIR, "assets", "images"),
    os.path.join(BASE_DIR, "data", "images"),
    os.path.join(BASE_DIR, "assets"),
    BASE_DIR,
]


def resolve_image(value: Any) -> str:
    """Turn the dataset's `filename` into a path that exists on disk."""
    if value is None:
        return ""
    raw = str(value).strip()
    if not raw or raw.lower() == "nan":
        return ""

    if os.path.isabs(raw) and os.path.isfile(raw):
        return raw

    candidate = os.path.join(BASE_DIR, raw)
    if os.path.isfile(candidate):
        return candidate

    basename = os.path.basename(raw)
    for folder in IMAGE_DIRS:
        candidate = os.path.join(folder, basename)
        if os.path.isfile(candidate):
            return candidate
    return ""


def normalise_score(value: Any) -> Optional[float]:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    if score > 1.0:  # already a percentage
        score = score / 100.0
    return max(0.0, min(1.0, score))


def normalise_keywords(value: Any) -> List[str]:
    """Keywords may be separated by commas, slashes, or pipes."""
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(v).strip() for v in value if str(v).strip()]

    text = str(value)
    if text.strip().lower() in ("", "nan"):
        return []
    for separator in (",", "|"):
        text = text.replace(separator, "/")
    return [part.strip() for part in text.split("/") if part.strip()]


def normalise(row: Dict[str, Any], position: int) -> Dict[str, Any]:
    filename = row.get("filename")

    category_tags = [titled(t) for t in split_tags(row.get("category"))]
    length_tags = [titled(t) for t in split_tags(row.get("hair_length"))]

    identifier = os.path.splitext(str(filename or ""))[0].strip()

    return {
        "id": identifier or f"style-{position}",
        "name": row.get("hairstyle_label") or "Untitled style",
        "description": str(row.get("description") or "").strip(),
        "category": " · ".join(category_tags),
        "hair_length": " · ".join(length_tags),
        "category_tags": category_tags,
        "length_tags": length_tags,
        "difficulty": str(row.get("difficulty") or "").strip(),
        "keywords": normalise_keywords(row.get("keywords")),
        "score": normalise_score(row.get("score")),
        "image_path": resolve_image(filename),
    }


# ---------------------------------------------------------------------------
# SEARCH ORCHESTRATION
# ---------------------------------------------------------------------------


def perform_search(query: str, filters: Dict[str, Any]):
    """Return (results, notice). Raises on engine failure; caller reports it.

    Filter choices go to the engine as real filter arguments rather than being
    folded into the query text — search_hairstyles already scores each filter
    dimension, so appending them to the query would double-count them.
    """
    results, notice = semantic_search.search_hairstyles(
        query=query.strip(),
        category=filters.get("occasion") or ALL,
        difficulty=filters.get("skill_level") or ALL,
        hair_length=filters.get("hair_length") or ALL,
        top_k=TOP_K,
    )
    rows = results.to_dict("records")
    return [normalise(row, i) for i, row in enumerate(rows)], notice


# SESSION STATE
# ---------------------------------------------------------------------------

DEFAULTS: Dict[str, Any] = {
    "page": "home",
    "results": [],
    "has_searched": False,
    "selected": None,
    "query": "",
    "f_occasion": None,
    "f_length": None,
    "f_skill": None,
    "notice": "",
    "engine_error": "",
}


def init_state() -> None:
    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def open_details(item: Dict[str, Any]) -> None:
    """Results stay in session state, so Back restores them without re-running."""
    st.session_state.selected = item
    st.session_state.page = "details"


def go_home() -> None:
    st.session_state.page = "home"
    st.session_state.selected = None


# ---------------------------------------------------------------------------
# VIEWS
# ---------------------------------------------------------------------------


def render_engine_notice() -> None:
    """Surface a real failure loudly rather than quietly showing nothing."""
    if ENGINE_IMPORT_ERROR is not None:
        st.error(
            "semantic_search.py could not be imported, so search is "
            f"unavailable.\n\n`{ENGINE_IMPORT_ERROR}`",
            icon="🚫",
        )
        return

    if st.session_state.engine_error:
        st.error(
            "The search engine returned an error.\n\n"
            f"`{st.session_state.engine_error}`",
            icon="🚫",
        )


def render_search_panel() -> None:
    options = filter_options()

    with st.container(border=True):
        ui.anchor("search-panel")
        ui.panel_title()

        col_occasion, col_length, col_skill, col_query = st.columns(
            [1, 1, 1, 1.25], gap="medium"
        )

        with col_occasion:
            ui.field_label(ui.ICON_OCCASION, "Occasion")
            st.selectbox(
                "Occasion",
                options["occasion"],
                index=None,
                placeholder="Select occasion",
                key="f_occasion",
                label_visibility="collapsed",
            )

        with col_length:
            ui.field_label(ui.ICON_LENGTH, "Hair Length")
            st.selectbox(
                "Hair length",
                options["hair_length"],
                index=None,
                placeholder="Select hair length",
                key="f_length",
                label_visibility="collapsed",
            )

        with col_skill:
            ui.field_label(ui.ICON_SKILL, "Skill Level")
            st.selectbox(
                "Skill level",
                options["skill"],
                index=None,
                placeholder="Select skill level",
                key="f_skill",
                label_visibility="collapsed",
            )

        with col_query:
            ui.field_label_spacer()
            st.text_input(
                "Describe your hairstyle",
                placeholder="Describe your hairstyle...",
                key="query",
                label_visibility="collapsed",
            )

        ui.spacer("sm")

        if st.button(
            "✨  Find My Hairstyle",
            type="primary",
            use_container_width=True,
            key="cta_search",
            disabled=ENGINE_IMPORT_ERROR is not None,
        ):
            filters = {
                "occasion": st.session_state.f_occasion,
                "hair_length": st.session_state.f_length,
                "skill_level": st.session_state.f_skill,
            }
            if ENGINE_IMPORT_ERROR is not None:
                return

            try:
                with st.spinner("Finding your perfect look..."):
                    results, notice = perform_search(
                        st.session_state.query, filters
                    )
                st.session_state.results = results
                st.session_state.notice = notice or ""
                st.session_state.engine_error = ""
            except Exception as exc:
                st.session_state.results = []
                st.session_state.notice = ""
                st.session_state.engine_error = str(exc)

            st.session_state.has_searched = True
            st.rerun()


def render_results() -> None:
    results = st.session_state.results

    if not results:
        ui.empty_state()
        return

    ui.results_header(len(results), st.session_state.query.strip())

    if st.session_state.notice:
        ui.search_notice(st.session_state.notice)

    for start in range(0, len(results), 3):
        row = results[start : start + 3]
        columns = st.columns(3, gap="large")
        for offset, item in enumerate(row):
            with columns[offset]:
                with st.container(border=True):
                    ui.anchor("style-card")
                    ui.style_card(item)
                    st.button(
                        "View Details",
                        key=f"details_{start + offset}_{item['id']}",
                        type="secondary",
                        use_container_width=True,
                        on_click=open_details,
                        args=(item,),
                    )
        ui.spacer("sm")


def render_home() -> None:
    ui.logo(LOGO_PATH)

    col_copy, col_art = st.columns([1.02, 0.98], gap="large")
    with col_copy:
        ui.hero_copy()
    with col_art:
        ui.hero_art(HERO_PATH)

    ui.spacer("md")
    render_engine_notice()
    render_search_panel()

    if st.session_state.has_searched:
        render_results()


def render_details() -> None:
    item = st.session_state.selected
    if not item:
        go_home()
        st.rerun()
        return

    ui.logo(LOGO_PATH)

    back_col, _ = st.columns([0.22, 0.78])
    with back_col:
        st.button(
            "←  Back to results",
            key="back_to_results",
            type="secondary",
            use_container_width=True,
            on_click=go_home,
        )

    ui.spacer("sm")

    col_media, col_body = st.columns([0.44, 0.56], gap="large")
    with col_media:
        with st.container(border=True):
            ui.anchor("detail-media")
            ui.detail_media(item)
    with col_body:
        with st.container(border=True):
            ui.anchor("detail-body")
            ui.detail_body(item)


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------


def main() -> None:
    ui.load_styles(STYLES_PATH)
    ui.background()
    init_state()

    if st.session_state.page == "details":
        render_details()
    else:
        render_home()


if __name__ == "__main__":
    main()