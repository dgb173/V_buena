"""
Streamlit UI tuned to mirror the layout shown in Screenshot_1.

Left side: matches loaded from data.json. Right side: the advanced analysis
cache (previews generados por reference_code) para el partido elegido. Pensado
para Render sin depender de navegadores; el scraping completo sigue siendo
opcional y defensivo.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import sys

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))
sys.path.insert(0, str(BASE_DIR / "scripts"))

# Live analysis is optional; keep a safe import guard so the app still runs on Render.
try:
    from modules.estudio_scraper import analizar_partido_completo  # type: ignore
except Exception:  # pragma: no cover - defensive for cloud deploys without Selenium
    analizar_partido_completo = None  # type: ignore

from scripts.scraping_logic import (
    get_main_page_finished_matches_async,
    get_main_page_matches_async,
)

DEFAULT_DATA_PATHS = [
    Path("data.json"),
    Path("src/data.json"),
]
PREVIEW_CACHE_DIRS = [
    Path("src/static/cached_previews"),
    Path("static/cached_previews"),
]


def _inject_global_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #eef2f9;
            --card: #ffffff;
            --primary: #2d6ce6;
            --away: #f97316;
            --muted: #5b667a;
            --chip-ah: #e8edff;
            --chip-ou: #e6f7ef;
        }
        .stApp {
            background: linear-gradient(180deg, #f7f9fd 0%, #eef2f9 100%);
            color: #0f172a;
        }
        .block-container { padding-top: 0.4rem; }
        h1, h2, h3, h4, h5, h6 { color: #0f172a; margin-bottom: 0.35rem; }
        .panel-card {
            background: var(--card);
            border-radius: 20px;
            padding: 20px 22px;
            box-shadow: 0 18px 48px rgba(15, 23, 42, 0.08);
            border: 1px solid #dde3f0;
        }
        .panel-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 1rem;
            flex-wrap: wrap;
        }
        .panel-title { font-size: 2rem; font-weight: 800; margin: 0; letter-spacing: -0.01em; }
        .eyebrow { color: var(--muted); text-transform: uppercase; letter-spacing: .1em; font-size: .78rem; margin: 0 0 6px 0; }
        .chips { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 6px; }
        .chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 11px;
            border-radius: 999px;
            font-weight: 700;
            font-size: 0.85rem;
            border: 1px solid #dbe5ff;
            background: #f5f7ff;
            color: #0f172a;
        }
        .chip.ah { background: var(--chip-ah); color: #1d4ed8; border-color: #c7d2fe; }
        .chip.ou { background: var(--chip-ou); color: #0f9d58; border-color: #b9f2d2; }
        .score-box {
            background: linear-gradient(135deg, #0f172a, #131c2e);
            color: #fff;
            border-radius: 14px;
            padding: 12px 16px;
            min-width: 160px;
            text-align: center;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.35);
        }
        .score-value { font-size: 1.9rem; font-weight: 800; letter-spacing: -0.02em; }
        .section-title { font-weight: 800; font-size: 1.2rem; margin: 14px 0 8px 0; display: flex; align-items: center; gap: 8px; }
        .section-subtle { color: var(--muted); font-size: 0.95rem; margin-bottom: 8px; }
        .grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; }
        .grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; }
        .mini-card {
            background: var(--card);
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 12px 14px;
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.05);
        }
        .mini-card h5, .mini-card h6 { margin: 0 0 6px 0; }
        .mini-stat-table { width: 100%; border-collapse: collapse; }
        .mini-stat-table td { padding: 3px 6px; font-size: 0.9rem; }
        .mini-stat-table td:first-child { font-weight: 700; color: var(--primary); }
        .mini-stat-table td:last-child { font-weight: 700; color: var(--away); text-align: right; }
        .cover-ok { color: #16a34a; font-weight: 800; }
        .cover-ko { color: #dc2626; font-weight: 800; }
        .cover-neutral { color: #6b7280; font-weight: 700; }
        .match-list { max-height: calc(100vh - 200px); overflow-y: auto; padding-right: 6px; }
        div[role="radiogroup"] { gap: 0.5rem; }
        div[role="radiogroup"] > label {
            background: #ffffff;
            border: 1px solid #d8e2f2;
            border-radius: 16px;
            padding: 10px 12px;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.07);
            transition: all .18s ease;
        }
        div[role="radiogroup"] > label:hover { border-color: var(--primary); box-shadow: 0 14px 30px rgba(45, 108, 230, 0.20); transform: translateY(-1px); }
        div[role="radiogroup"] input { display: none; }
        div[role="radiogroup"] > label[data-checked="true"],
        div[role="radiogroup"] > label[aria-checked="true"] {
            border: 2px solid var(--primary);
            box-shadow: 0 16px 36px rgba(45, 108, 230, 0.25);
        }
        div[role="radiogroup"] p { margin: 0; }
        .match-line { font-weight: 700; color: #0f172a; font-size: 0.98rem; }
        .match-sub { color: #475569; font-size: 0.86rem; margin-top: 2px; }
        .badge-ah { background: #eef2ff; color: #1d4ed8; padding: 3px 8px; border-radius: 999px; font-weight: 700; font-size: 0.78rem; }
        .badge-ou { background: #ecfdf3; color: #047857; padding: 3px 8px; border-radius: 999px; font-weight: 700; font-size: 0.78rem; margin-left: 6px; }
        .empty-card { padding: 12px; border: 1px dashed #cbd5e1; border-radius: 12px; background: #f8fafc; color: #475569; }
        .market-box { border: 1px dashed #cbd5e1; border-radius: 12px; padding: 12px; background: #f8fafc; }
        .hero-row { display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
        .hero-buttons { display: flex; gap: 0.6rem; flex-wrap: wrap; justify-content: flex-end; }
        .stButton > button {
            border-radius: 12px;
            font-weight: 700;
            padding: 0.65rem 1rem;
            border: 1px solid transparent;
            box-shadow: 0 10px 22px rgba(45, 108, 230, 0.25);
            background: linear-gradient(135deg, #2d6ce6, #2156ba);
            color: white;
        }
        .stButton > button:hover { filter: brightness(1.02); }
        .stButton.secondary > button {
            background: #ecf2ff;
            color: #2d6ce6;
            border: 1px solid #d7e3ff;
            box-shadow: none;
        }
        .pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 10px;
            background: #e9edf7;
            color: #1f2a44;
            border-radius: 10px;
            font-weight: 700;
            font-size: 0.9rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _parse_datetime(value: Any) -> Optional[datetime]:
    """Try to parse multiple date/time formats into a datetime instance."""
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _normalize_match(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure minimal fields exist and add derived display-friendly fields."""
    normalized = {
        "id": str(entry.get("id", "")),
        "home_team": entry.get("home_team", "N/A"),
        "away_team": entry.get("away_team", "N/A"),
        "handicap": entry.get("handicap", "N/A"),
        "goal_line": entry.get("goal_line", entry.get("goal_line_decimal", "N/A")),
        "score": entry.get("score"),
    }

    dt = _parse_datetime(entry.get("time_obj")) or _parse_datetime(entry.get("time"))
    if dt:
        normalized["time_obj"] = dt
        normalized["time"] = dt.strftime("%d/%m %H:%M")
    else:
        normalized["time_obj"] = None
        normalized["time"] = entry.get("time", "N/A")

    return normalized


def _load_from_disk() -> Tuple[Dict[str, List[Dict[str, Any]]], Optional[Path]]:
    for candidate in DEFAULT_DATA_PATHS:
        if candidate.exists():
            with candidate.open("r", encoding="utf-8") as fh:
                return json.load(fh), candidate
    return {"upcoming_matches": [], "finished_matches": []}, None


@st.cache_data(show_spinner=False)
def load_dataset(upload_file: Optional[bytes]) -> Tuple[Dict[str, List[Dict[str, Any]]], str]:
    """
    Load data from an uploaded JSON (if provided) or from disk.
    Returns the normalized dataset and a label describing the source.
    """
    if upload_file is not None:
        data = json.loads(upload_file.decode("utf-8"))
        source = "Archivo subido"
    else:
        data, path_used = _load_from_disk()
        source = f"Local: {path_used}" if path_used else "Vacio (sin data.json)"

    upcoming = [_normalize_match(m) for m in data.get("upcoming_matches", []) if isinstance(m, dict)]
    finished = [_normalize_match(m) for m in data.get("finished_matches", []) if isinstance(m, dict)]

    return {"upcoming_matches": upcoming, "finished_matches": finished}, source


def _scrape_live(limit_upcoming: int = 30, limit_finished: int = 30) -> Dict[str, List[Dict[str, Any]]]:
    """
    Best-effort scraping using the lightweight logic (requests first, Playwright fallback).
    If Playwright browsers are not available in the environment, it will still return what
    requests can fetch.
    """
    try:
        upcoming = asyncio.run(get_main_page_matches_async(limit=limit_upcoming))
        finished = asyncio.run(get_main_page_finished_matches_async(limit=limit_finished))
        return {
            "upcoming_matches": [_normalize_match(m) for m in upcoming if isinstance(m, dict)],
            "finished_matches": [_normalize_match(m) for m in finished if isinstance(m, dict)],
        }
    except Exception as exc:
        st.error(f"No se pudo scrapear en vivo: {exc}")
        return {"upcoming_matches": [], "finished_matches": []}


def _load_cached_preview(match_id: str) -> Optional[Dict[str, Any]]:
    if not match_id:
        return None
    for base in PREVIEW_CACHE_DIRS:
        path = base / f"{match_id}.json"
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
    return None


def _format_match_label(match: Dict[str, Any]) -> str:
    time_txt = match.get("time", "N/D")
    names = f"{match.get('home_team', '-') } vs {match.get('away_team', '-')}"
    ah = match.get("handicap", "N/A")
    gl = match.get("goal_line", "N/A")
    return f"{time_txt} | {names}\nAH {ah}   /   O/U {gl}"


def _filter_matches(matches: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    if not query:
        return matches
    q = query.lower().strip()
    return [
        m for m in matches
        if q in str(m.get("home_team", "")).lower()
        or q in str(m.get("away_team", "")).lower()
    ]


def _sort_matches(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(matches, key=lambda x: x.get("time_obj") or datetime.max)


def _find_match_by_id(all_matches: List[Dict[str, Any]], match_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not match_id:
        return None
    for m in all_matches:
        if str(m.get("id")) == str(match_id):
            return m
    return None


def _cover_badge(status: Optional[str]) -> str:
    if not status:
        return ""
    status = status.upper()
    if status == "CUBIERTO":
        return '<span class="cover-ok">CUBIERTO</span>'
    if status in ("NO CUBIERTO", "NO_CUBIERTO"):
        return '<span class="cover-ko">NO CUBIERTO</span>'
    if status in ("PUSH", "NULO", "NEUTRO"):
        return '<span class="cover-neutral">PUSH</span>'
    return f'<span class="cover-neutral">{status}</span>'


def _stat_rows_table(rows: Optional[List[Dict[str, Any]]]) -> str:
    if not rows:
        return ""
    html_rows = []
    for stat in rows:
        html_rows.append(
            f"<tr><td>{stat.get('home', '')}</td>"
            f"<td style='text-align:center;color:#6b7280;font-weight:600;'>{stat.get('label', '')}</td>"
            f"<td>{stat.get('away', '')}</td></tr>"
        )
    return f"<table class='mini-stat-table'>{''.join(html_rows)}</table>"


def _recent_card(title: str, payload: Optional[Dict[str, Any]], accent_class: str) -> str:
    if not payload:
        return f"<div class='mini-card'><h6>{title}</h6><div class='empty-card'>Sin datos disponibles.</div></div>"
    score = payload.get("score", "-")
    ah = payload.get("ah", "-")
    ou = payload.get("ou", "-")
    cover = _cover_badge(payload.get("cover_status"))
    stats = _stat_rows_table(payload.get("stats_rows"))
    date_txt = payload.get("date", "")
    return (
        f"<div class='mini-card'>"
        f"<h6 class='{accent_class}'>{title}</h6>"
        f"<div style='font-size:1.1rem;font-weight:800;margin-bottom:4px;'>{score}</div>"
        f"<div class='match-sub'>{payload.get('home','-')} vs {payload.get('away','-')}</div>"
        f"<div class='match-sub'>{date_txt}</div>"
        f"<div class='match-sub'>AH: <strong>{ah}</strong> / O/U: <strong>{ou}</strong></div>"
        f"<div style='margin:4px 0;'>{cover}</div>"
        f"{stats}"
        f"</div>"
    )


def _recent_section(analysis: Dict[str, Any]) -> str:
    data = analysis.get("recent_indirect_full") or {}
    html_blocks = []
    html_blocks.append(_recent_card("Ultimo local (casa)", data.get("last_home"), "home-color"))
    html_blocks.append(_recent_card("Ultimo visitante (fuera)", data.get("last_away"), "away-color"))
    html_blocks.append(_recent_card("H2H referencia", data.get("h2h_col3"), "match-sub"))
    return "<div class='grid-3'>" + "".join(html_blocks) + "</div>"


def _comparativas_section(analysis: Dict[str, Any]) -> str:
    comps = analysis.get("comparativas_indirectas") or {}
    left = comps.get("left")
    right = comps.get("right")
    if not left and not right:
        return "<div class='empty-card'>Sin comparativas indirectas guardadas.</div>"

    def _card(label: str, payload: Dict[str, Any]) -> str:
        if not payload:
            return f"<div class='mini-card'><h6>{label}</h6><div class='empty-card'>No disponible.</div></div>"
        stats = _stat_rows_table(payload.get("stats_rows"))
        cover = _cover_badge(payload.get("cover_status"))
        analysis_line = payload.get("analysis", "")
        return (
            f"<div class='mini-card'>"
            f"<h6>{label}</h6>"
            f"<div class='match-line'>{payload.get('score','-')}</div>"
            f"<div class='match-sub'>{payload.get('home_team','-')} vs {payload.get('away_team','-')}</div>"
            f"<div class='match-sub'>AH: <strong>{payload.get('ah','-')}</strong> / O/U: <strong>{payload.get('ou','-')}</strong></div>"
            f"<div class='match-sub'>Localia: <strong>{payload.get('localia','-')}</strong></div>"
            f"<div style='margin:4px 0;'>{cover}</div>"
            f"{stats}"
            f"{f'<div class=\"match-sub\" style=\"margin-top:6px;\">{analysis_line}</div>' if analysis_line else ''}"
            f"</div>"
        )

    cards = [
        _card("Local vs ultimo rival visitante", left),
        _card("Visitante vs ultimo rival local", right),
    ]
    return "<div class='grid-2'>" + "".join(cards) + "</div>"


def _standings_section(analysis: Dict[str, Any], home: str, away: str) -> str:
    home_std = analysis.get("home_standings")
    away_std = analysis.get("away_standings")
    home_ou = analysis.get("home_ou_stats", {})
    away_ou = analysis.get("away_ou_stats", {})
    if not home_std and not away_std and not home_ou and not away_ou:
        return "<div class='empty-card'>Sin datos de clasificacion/Over-Under en el analisis cacheado.</div>"

    def _block(title: str, std: Dict[str, Any], ou_stats: Dict[str, Any], accent: str) -> str:
        parts = [f"<div class='{accent}' style='font-weight:800;font-size:1.05rem;'>{title}</div>"]
        if std:
            parts.append(
                f"<div class='match-sub'>Posicion: <strong>{std.get('ranking','-')}</strong></div>"
                f"<div class='match-sub'>PJ: {std.get('total_pj','-')} | V-E-D: {std.get('total_v','-')}-{std.get('total_e','-')}-{std.get('total_d','-')} | GF:GC {std.get('total_gf','-')}:{std.get('total_gc','-')}</div>"
            )
            if std.get("specific_type"):
                parts.append(
                    f"<div class='match-sub'>{std.get('specific_type')}: PJ {std.get('specific_pj','-')} | V-E-D {std.get('specific_v','-')}-{std.get('specific_e','-')}-{std.get('specific_d','-')} | GF:GC {std.get('specific_gf','-')}:{std.get('specific_gc','-')}</div>"
                )
        if ou_stats and ou_stats.get("total"):
            parts.append(
                f"<div class='match-sub'>O/U ult. {ou_stats.get('total')} part.: "
                f"<span style='color:#16a34a;font-weight:800;'>Over {ou_stats.get('over_pct','-')}%</span> / "
                f"<span style='color:#dc2626;font-weight:800;'>Under {ou_stats.get('under_pct','-')}%</span> / "
                f"<span style='color:#6b7280;font-weight:700;'>Push {ou_stats.get('push_pct','-')}%</span></div>"
            )
        return "<div class='mini-card'>" + "".join(parts) + "</div>"

    blocks = []
    blocks.append(_block(home, home_std or {}, home_ou or {}, "home-color"))
    blocks.append(_block(away, away_std or {}, away_ou or {}, "away-color"))
    return "<div class='grid-2'>" + "".join(blocks) + "</div>"


def render_analysis_panel(
    match: Optional[Dict[str, Any]],
    analysis: Optional[Dict[str, Any]],
    source_label: str,
) -> None:
    if not match:
        st.info("Selecciona un partido para ver su analisis.")
        return

    home_name = (analysis or {}).get("home_name") or (analysis or {}).get("home_team") or match.get("home_team", "-")
    away_name = (analysis or {}).get("away_name") or (analysis or {}).get("away_team") or match.get("away_team", "-")
    ah = match.get("handicap", "N/A")
    gl = match.get("goal_line", "N/A")
    score = (analysis or {}).get("final_score") or match.get("score") or "-"
    display_time = (analysis or {}).get("match_time") or (analysis or {}).get("match_date") or match.get("time", "-")

    sections: List[str] = []
    sections.append(f"<div class='section-title'>Analisis de Partido Avanzado</div>")

    if analysis:
        sections.append(_standings_section(analysis, home_name, away_name))
        sections.append("<div class='section-title'>Historial inmediato</div>")
        sections.append(_recent_section(analysis))
        sections.append("<div class='section-title'>Comparativas indirectas</div>")
        sections.append(_comparativas_section(analysis))

        market_html = analysis.get("simplified_html") or analysis.get("market_analysis_html")
        if market_html:
            sections.append("<div class='section-title'>Vista de mercado / H2H</div>")
            sections.append(f"<div class='market-box'>{market_html}</div>")
    else:
        sections.append("<div class='empty-card'>No hay analisis cacheado para este partido. Puedes subir un JSON de analisis o generarlo en tu entorno local.</div>")

    panel_html = f"""
    <div class="panel-card">
        <div class="panel-header">
            <div>
                <p class="eyebrow">Fuente de datos: {source_label}</p>
                <div class="panel-title">{home_name} vs {away_name}</div>
                <div class="chips">
                    <span class="chip ah">AH {ah}</span>
                    <span class="chip ou">O/U {gl}</span>
                </div>
                <div class="match-sub" style="margin-top:6px;">ID {match.get('id','-')} | {display_time}</div>
            </div>
            <div class="score-box">
                <div class="match-sub" style="color:#cbd5e1;">Marcador</div>
                <div class="score-value">{score}</div>
            </div>
        </div>
        {''.join(sections)}
    </div>
    """

    st.markdown(panel_html, unsafe_allow_html=True)

    if analysis:
        with st.expander("Ver JSON de analisis"):
            st.json(analysis)


def main() -> None:
    st.set_page_config(page_title="Panel de Partidos", layout="wide")
    _inject_global_styles()

    st.title("Panel de partidos")
    st.caption("Replica visual de Screenshot_1: lista a la izquierda y analisis cache (reference_code) a la derecha.")

    # Estado inicial de dataset y fuente
    if "active_dataset" not in st.session_state:
        initial_data, initial_source = load_dataset(None)
        st.session_state["active_dataset"] = initial_data
        st.session_state["data_source_label"] = initial_source

    dataset = st.session_state["active_dataset"]
    source_label = st.session_state.get("data_source_label", "Sin fuente")
    active_preview_id = st.session_state.get("active_preview_match_id")
    selected_match_id_state = st.session_state.get("selected_match_id")

    header_col, actions_col = st.columns([1.7, 1.3], gap="large")
    with header_col:
        st.markdown("### Analisis de Partido Avanzado")
        st.markdown(
            f"<div class='pill'>Fuente datos: {source_label}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p class='section-subtle'>Proximos: {len(dataset['upcoming_matches'])} | Finalizados: {len(dataset['finished_matches'])}</p>",
            unsafe_allow_html=True,
        )

    # Controles de accion principales
    with actions_col:
        c1, c2 = st.columns(2, gap="small")
        with c1:
            preview_btn = st.button("Vista previa rapida", use_container_width=True, key="btn_preview")
        with c2:
            refresh_btn = st.button("Actualizar datos", use_container_width=True, key="btn_refresh")

        uploaded_dataset_bytes: Optional[bytes] = None
        uploaded_preview_bytes: Optional[bytes] = None
        with st.expander("Cargar JSON (data o preview) / opciones", expanded=False):
            upload_dataset = st.file_uploader("Sube tu data.json", type=["json"])
            upload_preview = st.file_uploader("Sube un analisis JSON (opcional)", type=["json"], key="preview_uploader_new")
            col_up, col_reset = st.columns(2, gap="small")
            if upload_dataset:
                uploaded_dataset_bytes = upload_dataset.read()
                col_up.info("Archivo listo para cargar.")
            if upload_preview:
                uploaded_preview_bytes = upload_preview.read()
                col_up.info("Preview JSON listo para usar.")

            if col_up.button("Usar data subida", use_container_width=True):
                if uploaded_dataset_bytes:
                    new_data, new_source = load_dataset(uploaded_dataset_bytes)
                    st.session_state["active_dataset"] = new_data
                    st.session_state["data_source_label"] = new_source
                    dataset, source_label = new_data, new_source
                    st.success("Dataset cargado.")
                else:
                    st.warning("No hay data.json subido.")
            if col_reset.button("Recargar data local", use_container_width=True):
                load_dataset.clear()
                new_data, new_source = load_dataset(None)
                st.session_state["active_dataset"] = new_data
                st.session_state["data_source_label"] = new_source
                dataset, source_label = new_data, new_source
                st.success("Dataset recargado.")

        if refresh_btn:
            with st.spinner("Actualizando listas (ligero)..."):
                live_data = _scrape_live(limit_upcoming=40, limit_finished=40)
            st.session_state["active_dataset"] = live_data
            st.session_state["data_source_label"] = "Scrape en vivo (ligero)"
            dataset, source_label = live_data, "Scrape en vivo (ligero)"
            st.success("Listas actualizadas.")

    all_matches = dataset["upcoming_matches"] + dataset["finished_matches"]

    list_col, panel_col = st.columns([0.95, 2.05], gap="large")

    with list_col:
        st.markdown("#### Partidos (data.json)")
        tab_choice = st.radio(
            "Tipo de lista",
            options=["Proximos", "Finalizados", "Todos"],
            index=0,
            horizontal=True,
            label_visibility="collapsed",
        )
        search = st.text_input("Buscar equipo", "", placeholder="Escribe un nombre...", label_visibility="collapsed")

        if tab_choice == "Proximos":
            matches = _filter_matches(dataset["upcoming_matches"], search)
        elif tab_choice == "Finalizados":
            matches = _filter_matches(dataset["finished_matches"], search)
        else:
            matches = _filter_matches(all_matches, search)

        matches = _sort_matches(matches)
        st.markdown(f"<p class='section-subtle'>Mostrando {len(matches)} partidos</p>", unsafe_allow_html=True)

        options_ids = [m["id"] for m in matches]
        match_lookup = {m["id"]: m for m in matches}
        default_index = 0
        if selected_match_id_state in options_ids:
            default_index = options_ids.index(selected_match_id_state)

        if options_ids:
            selected_match_id = st.radio(
                "Partidos",
                options=options_ids,
                format_func=lambda mid: _format_match_label(match_lookup[mid]),
                index=default_index,
                label_visibility="collapsed",
                key="match_selector",
            )
            st.session_state["selected_match_id"] = selected_match_id
        else:
            st.info("No hay partidos con los filtros actuales.")
            selected_match_id = None

    with panel_col:
        # Determinar si se debe cargar preview
        if preview_btn and selected_match_id_state:
            st.session_state["active_preview_match_id"] = selected_match_id_state
            active_preview_id = selected_match_id_state
        elif preview_btn and not selected_match_id_state:
            st.warning("Elige un partido antes de pedir la vista previa.")

        selected_match = _find_match_by_id(all_matches, active_preview_id)
        analysis_data = None
        analysis_source = "Sin analisis cacheado"

        if uploaded_preview_bytes:
            try:
                analysis_data = json.loads(uploaded_preview_bytes.decode("utf-8"))
                analysis_source = "JSON subido"
            except Exception:
                st.warning("No se pudo leer el JSON de analisis subido.")
        if not analysis_data and active_preview_id:
            analysis_data = _load_cached_preview(active_preview_id)
            if analysis_data:
                analysis_source = "Cache local"

        if not active_preview_id:
            st.info("Selecciona un partido y pulsa 'Vista previa rapida' para mostrar el panel de reference_code.")
        else:
            render_analysis_panel(selected_match, analysis_data, analysis_source)


if __name__ == "__main__":
    main()
