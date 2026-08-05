"""
components.py — ANNIST presentation layer.

Every function here either returns an HTML string or writes one to the page.
No business logic, no search, no session-state mutation: app.py owns those.

HTML rule: markup is passed through `_html()`, which strips the leading
whitespace from every line before it reaches st.markdown(). Indented HTML
would otherwise be parsed as a Markdown code block.
"""

from __future__ import annotations

import base64
import html as _htmlmod
import os
from typing import Any, Iterable

import streamlit as st

# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------


def _html(markup: str) -> str:
    """Strip indentation from every line so Markdown never sees a code block."""
    return "\n".join(
        line.strip() for line in markup.strip().splitlines() if line.strip()
    )


def write(markup: str) -> None:
    """Render a block of raw HTML."""
    st.markdown(_html(markup), unsafe_allow_html=True)


def esc(value: Any) -> str:
    """Escape user/dataset text before it goes into markup."""
    return _htmlmod.escape(str(value if value is not None else ""), quote=True)


def anchor(name: str) -> None:
    """Invisible marker that lets CSS identify the container it sits in.

    Streamlit 1.37 puts `stVerticalBlockBorderWrapper` on *every* vertical
    block, not only on st.container(border=True), so the glass panel style is
    scoped to these anchors via :has() rather than to that test id alone.
    """
    write(f'<span class="anchor anchor-panel anchor-{esc(name)}"></span>')


def spacer(size: str = "md") -> None:
    write(f'<div class="spacer-{esc(size)}"></div>')


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------

_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
}


@st.cache_data(show_spinner=False)
def data_uri(path: str) -> str:
    """Read an image from disk and return a base64 data URI. '' if unavailable."""
    if not path or not os.path.isfile(path):
        return ""
    mime = _MIME.get(os.path.splitext(path)[1].lower(), "image/png")
    try:
        with open(path, "rb") as handle:
            encoded = base64.b64encode(handle.read()).decode("ascii")
    except OSError:
        return ""
    return f"data:{mime};base64,{encoded}"


def load_styles(path: str) -> None:
    """Inject styles.css. Falls back silently so the app never hard-fails."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            css = handle.read()
    except OSError:
        st.warning("styles.css could not be read — the app is running unstyled.")
        return
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Icons (inline SVG — no icon font dependency)
# ---------------------------------------------------------------------------

SPARK_GOLD = (
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none">'
    '<path d="M12 2.6l1.9 5.6 5.6 1.9-5.6 1.9L12 17.6l-1.9-5.6-5.6-1.9 5.6-1.9L12 2.6z" '
    'fill="#E0A63A"/>'
    '<circle cx="19.4" cy="4.6" r="1.1" fill="#F7CB7F"/>'
    "</svg>"
)

SPARK_PINK_LG = (
    '<svg width="44" height="44" viewBox="0 0 24 24" fill="none">'
    '<path d="M12 1.8l2.3 6.6 6.6 2.3-6.6 2.3L12 19.6l-2.3-6.6-6.6-2.3 6.6-2.3L12 1.8z" '
    'fill="#FA9CC0"/></svg>'
)

SPARK_PINK_SM = (
    '<svg width="26" height="26" viewBox="0 0 24 24" fill="none">'
    '<path d="M12 3l1.8 5.4 5.4 1.8-5.4 1.8L12 17.4l-1.8-5.4L4.8 10.2l5.4-1.8L12 3z" '
    'fill="#FBC4D6"/></svg>'
)

SPARK_WHITE = (
    '<svg width="22" height="22" viewBox="0 0 24 24" fill="none">'
    '<path d="M12 2.8l1.9 5.5 5.5 1.9-5.5 1.9L12 17.6l-1.9-5.5-5.5-1.9 5.5-1.9L12 2.8z" '
    'fill="#FFFFFF"/></svg>'
)

ICON_CARD_SPARK = (
    '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#F0428A" '
    'stroke-width="1.5" stroke-linejoin="round">'
    '<path d="M12 3l2.2 6.8L21 12l-6.8 2.2L12 21l-2.2-6.8L3 12l6.8-2.2L12 3z"/></svg>'
)

ICON_OCCASION = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#F0428A" '
    'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="3" y="5" width="18" height="16" rx="3"/>'
    '<path d="M3 10h18M8 3v4M16 3v4"/></svg>'
)

ICON_LENGTH = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#F0428A" '
    'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M12 3a6 6 0 0 0-6 6v6a3 3 0 0 0 6 0"/>'
    '<path d="M12 3a6 6 0 0 1 6 6v6a3 3 0 0 1-6 0"/></svg>'
)

ICON_SKILL = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#F0428A" '
    'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.3-4.1 '
    "5.9-.9L12 3.5z\"/></svg>"
)

ICON_SEARCH = (
    '<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#F0428A" '
    'stroke-width="1.9" stroke-linecap="round">'
    '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/></svg>'
)

ICON_IMAGE_PLACEHOLDER = (
    '<svg width="46" height="46" viewBox="0 0 24 24" fill="none" stroke="#FA9CC0" '
    'stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="3" y="4" width="18" height="16" rx="3"/>'
    '<circle cx="9" cy="10" r="1.8"/><path d="M4 18l5-5 4 4 3-2.5 4 3.5"/></svg>'
)

ICON_EMPTY = (
    '<svg width="54" height="54" viewBox="0 0 24 24" fill="none" stroke="#FBC4D6" '
    'stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="11" cy="11" r="7"/><path d="M16.5 16.5L21 21"/>'
    '<path d="M8.5 11h5"/></svg>'
)


# ---------------------------------------------------------------------------
# Chrome
# ---------------------------------------------------------------------------


def background() -> None:
    """Fixed decorative blobs behind the whole app."""
    write(
        """
        <div class="annist-bg"><span></span><span></span><span></span></div>
        """
    )


def logo(path: str = "assets/logo.png") -> None:
    uri = data_uri(path)
    if uri:
        write(
            '<div class="annist-logo">'
            f'<img src="{uri}" alt="ANNIST — Hair AI" />'
            "</div>"
        )
    else:
        write(
            '<div class="annist-logo">'
            '<div class="annist-logo-fallback">Annist<small>HAIR AI</small></div>'
            "</div>"
        )


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------


def hero_copy() -> None:
    """Eyebrow, headline, script line and the glass intro card."""
    write(
        '<div class="hero">'
        f'<div class="hero-eyebrow">{SPARK_GOLD}Welcome to ANNIST</div>'
        '<h1 class="hero-title">Your Perfect Hairstyle'
        f'<span class="spark-inline">{SPARK_PINK_SM}</span></h1>'
        '<div class="hero-script">starts here</div>'
        '<div class="hero-card">'
        f'<div class="hero-card-badge">{ICON_CARD_SPARK}</div>'
        '<div class="hero-card-body">'
        "<p>ANNIST is your intelligent hairstyle recommendation assistant. "
        "Discover beautiful hairstyles tailored to your occasion, hair length "
        "and styling experience using AI-powered semantic search.</p>"
        "<hr />"
        "<p>Whether you're preparing for a wedding, university, work, travelling "
        "or simply looking for your next everyday hairstyle, ANNIST helps you "
        "discover beautiful looks within seconds.</p>"
        "</div></div></div>"
    )


def hero_art(path: str = "assets/hero_illustration.png") -> None:
    uri = data_uri(path)
    if uri:
        write(
            '<div class="hero-art">'
            f'<img src="{uri}" alt="Illustration of a woman wearing a soft updo" />'
            "</div>"
        )
    else:
        write(
            '<div class="hero-art">'
            '<div class="hero-art-fallback"></div>'
            "</div>"
        )


# ---------------------------------------------------------------------------
# Search panel
# ---------------------------------------------------------------------------


def panel_title(text: str = "Let's find your perfect look") -> None:
    write(
        '<div class="panel-title">'
        f"{SPARK_GOLD}{esc(text)}{SPARK_GOLD}"
        "</div>"
    )


def field_label(icon: str, text: str) -> None:
    write(
        '<div class="field-label">'
        f'<span class="icon">{icon}</span><span>{esc(text)}</span>'
        "</div>"
    )


def field_label_spacer() -> None:
    """Keeps the free-text field baseline-aligned with the labelled selects."""
    write('<div class="field-label field-label--spacer"><span>&nbsp;</span></div>')


# ---------------------------------------------------------------------------
# Badges
# ---------------------------------------------------------------------------

_DIFFICULTY_CLASS = {
    "easy": "badge--easy",
    "beginner": "badge--easy",
    "simple": "badge--easy",
    "medium": "badge--medium",
    "intermediate": "badge--medium",
    "moderate": "badge--medium",
    "hard": "badge--hard",
    "advanced": "badge--hard",
    "expert": "badge--hard",
    "difficult": "badge--hard",
}


def difficulty_class(value: Any) -> str:
    return _DIFFICULTY_CLASS.get(str(value or "").strip().lower(), "badge--medium")


def badge(text: Any, variant: str) -> str:
    if not str(text or "").strip():
        return ""
    return f'<span class="badge {variant}">{esc(text)}</span>'


def badge_row(item: dict) -> str:
    """One badge per tag — the dataset packs several per cell (e.g. wedding/party)."""
    parts = []
    for tag in (item.get("category_tags") or [])[:2]:
        parts.append(badge(tag, "badge--category"))
    for tag in (item.get("length_tags") or [])[:2]:
        parts.append(badge(tag, "badge--length"))
    parts.append(
        badge(item.get("difficulty"), difficulty_class(item.get("difficulty")))
    )
    inner = "".join(p for p in parts if p)
    return f'<div class="badge-row">{inner}</div>' if inner else ""


def search_notice(text: str) -> None:
    """The engine's relaxation message, e.g. when no exact match existed."""
    write(f'<p class="search-notice">{esc(text)}</p>')


def chips(values: Iterable[str]) -> str:
    items = [str(v).strip() for v in values if str(v).strip()]
    if not items:
        return ""
    inner = "".join(f'<span class="chip">{esc(v)}</span>' for v in items)
    return f'<div class="chip-row">{inner}</div>'


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------


def results_header(count: int, query: str = "") -> None:
    noun = "hairstyle" if count == 1 else "hairstyles"
    if query:
        sub = f"Matched to <em>{esc(query)}</em>, ranked by semantic similarity."
    else:
        sub = "Ranked by how closely each look matches your choices."
    write(
        '<div class="results-head">'
        f"<h2>{count} {noun} for you</h2>"
        f"<p>{sub}</p>"
        "</div>"
    )


def _media(item: dict, wrapper_class: str, show_score: bool) -> str:
    uri = data_uri(item.get("image_path") or "")
    if uri:
        inner = f'<img src="{uri}" alt="{esc(item.get("name"))}" />'
    else:
        inner = f'<div class="placeholder">{ICON_IMAGE_PLACEHOLDER}</div>'

    pill = ""
    if show_score and item.get("score") is not None:
        pct = int(round(float(item["score"]) * 100))
        pill = f'<span class="score-pill">{SPARK_PINK_SM}{pct}% match</span>'

    return f'<div class="{wrapper_class}">{inner}{pill}</div>'


def style_card(item: dict) -> None:
    """Card body. app.py renders the View Details button directly beneath it."""
    desc = str(item.get("description") or "").strip()
    write(
        _media(item, "style-card-media", show_score=True)
        + f'<h3 class="style-card-title">{esc(item.get("name") or "Untitled style")}</h3>'
        + (f'<p class="style-card-desc">{esc(desc)}</p>' if desc else "")
        + badge_row(item)
    )


def empty_state(message: str = "No hairstyles matched those choices") -> None:
    write(
        '<div class="empty-state">'
        f"{ICON_EMPTY}"
        f"<h3>{esc(message)}</h3>"
        "<p>Try widening a filter, or describe the look you want in your own words.</p>"
        "</div>"
    )


# ---------------------------------------------------------------------------
# Details page
# ---------------------------------------------------------------------------


def detail_media(item: dict) -> None:
    write(_media(item, "detail-media", show_score=False))


def detail_body(item: dict) -> None:
    score = item.get("score")
    blocks = [
        '<p class="detail-eyebrow">Hairstyle detail</p>',
        f'<h2 class="detail-title">{esc(item.get("name") or "Untitled style")}</h2>',
        badge_row(item),
    ]

    if score is not None:
        pct = max(0, min(100, int(round(float(score) * 100))))
        blocks.append(
            f'<div class="match-score"><div class="match-ring" style="--pct:{pct}">'
            f"<i>{pct}%</i></div><div class=\"match-copy\">"
            "<strong>AI match score</strong>"
            "<span>How closely this look fits what you asked for.</span>"
            "</div></div>"
        )

    description = str(item.get("description") or "").strip()
    if description:
        blocks.append('<div class="detail-section-title">About this look</div>')
        blocks.append(f'<p class="detail-desc">{esc(description)}</p>')

    keywords = item.get("keywords") or []
    chip_markup = chips(keywords)
    if chip_markup:
        blocks.append('<div class="detail-section-title">Keywords</div>')
        blocks.append(chip_markup)

    write("".join(blocks))