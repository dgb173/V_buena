"""
Streamlit viewer for scraped match data.

The app reads a `data.json` file (either uploaded by the user or already
present in the repo) and renders upcoming/finished matches with basic
filters. It also has an optional light scrape (requests-first, Playwright
fallback) to refrescar las listas si el entorno lo permite.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import sys

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))
sys.path.insert(0, str(BASE_DIR / "scripts"))

from scripts.scraping_logic import (
    get_main_page_finished_matches_async,
    get_main_page_matches_async,
)
from modules.estudio_scraper import analizar_partido_completo


DEFAULT_DATA_PATHS = [
    Path("data.json"),
    Path("src/data.json"),
]
PREVIEW_CACHE_DIRS = [
    Path("src/static/cached_previews"),
    Path("static/cached_previews"),
]


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
    # Fallback: isoformat parser
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


def _build_filter_options(matches: List[Dict[str, Any]], field: str) -> List[str]:
    values = sorted({str(m.get(field)) for m in matches if m.get(field) not in (None, "", "N/A")})
    return ["(Todos)"] + values


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


def _render_preview(data: Dict[str, Any]) -> None:
    st.subheader("Analisis completo (cache)")
    if not data:
        st.info("No hay cache de analisis para este partido. Sube un JSON o generalo antes en tu entorno.")
        return

    meta_cols = st.columns(3)
    meta_cols[0].metric("Local", data.get("home_team", "-"))
    meta_cols[1].metric("Visitante", data.get("away_team", "-"))
    meta_cols[2].metric("Marcador", data.get("final_score") or data.get("score") or "-")

    if data.get("match_time") or data.get("match_date"):
        st.caption(f"Fecha: {data.get('match_date', '-')}, Hora: {data.get('match_time', '-')}")

    if data.get("simplified_html"):
        st.markdown("Vista simplificada", help="Generada por el analisis original")
        st.components.v1.html(data["simplified_html"], height=600, scrolling=True)
    else:
        st.markdown("Datos (JSON)")
        st.json(data)


def _render_live_analysis(match_id: str) -> None:
    if not match_id:
        st.info("Introduce un ID de partido para analizar en vivo.")
        return
    with st.spinner("Analizando en vivo (requiere navegador/Playwright/driver) ..."):
        try:
            data = analizar_partido_completo(match_id)
        except Exception as exc:
            st.error(f"No se pudo analizar el partido {match_id}: {exc}")
            return

    if not isinstance(data, dict):
        st.error("El analisis no devolvio datos validos.")
        return
    if data.get("error"):
        st.error(f"Error del analisis: {data.get('error')}")
        return

    st.success(f"Analisis completado para ID {match_id}")
    header = st.columns(3)
    header[0].metric("Local", data.get("home_name", "-"))
    header[1].metric("Visitante", data.get("away_name", "-"))
    header[2].metric("Marcador", data.get("final_score") or data.get("score") or "-")

    if data.get("market_analysis_html"):
        st.markdown("Vista de mercado")
        st.components.v1.html(data["market_analysis_html"], height=500, scrolling=True)

    st.markdown("Datos completos")
    st.json(data)


def _filter_matches(
    matches: List[Dict[str, Any]],
    search: str,
    handicap: str,
    goal_line: str,
    only_future: bool,
) -> List[Dict[str, Any]]:
    search_lower = search.lower().strip()
    results = []
    now = datetime.utcnow()

    for m in matches:
        if only_future and isinstance(m.get("time_obj"), datetime) and m["time_obj"] < now:
            continue
        if search_lower:
            if search_lower not in str(m.get("home_team", "")).lower() \
               and search_lower not in str(m.get("away_team", "")).lower():
                continue
        if handicap and handicap != "(Todos)" and str(m.get("handicap")) != handicap:
            continue
        if goal_line and goal_line != "(Todos)" and str(m.get("goal_line")) != goal_line:
            continue
        results.append(m)

    results.sort(key=lambda x: x.get("time_obj") or datetime.max)
    return results


def _render_list(title: str, matches: List[Dict[str, Any]]) -> None:
    st.subheader(title, divider="gray")
    if not matches:
        st.info("No hay partidos para mostrar con los filtros actuales.")
        return

    for m in matches:
        cols = st.columns([3, 2, 2, 2])
        with cols[0]:
            st.markdown(f"**{m['home_team']}** vs **{m['away_team']}**")
            st.caption(f"ID: {m['id']}")
        with cols[1]:
            st.markdown(f"Hora: {m.get('time', 'N/A')}")
        with cols[2]:
            st.markdown(f"AH: `{m.get('handicap', 'N/A')}`")
        with cols[3]:
            gl = m.get("goal_line", "N/A")
            st.markdown(f"Goles: `{gl}`")
        if m.get("score"):
            st.write(f"Marcador: **{m['score']}**")
        st.divider()


def main() -> None:
    st.set_page_config(page_title="Panel de Partidos", layout="wide")
    st.title("Partidos - Streamlit")
    st.caption("Visor ligero usando los datos ya scrapeados (data.json).")

    with st.sidebar:
        st.header("Fuente de datos")
        upload = st.file_uploader("Sube tu data.json", type=["json"])
        dataset, source_label = load_dataset(upload.read() if upload else None)
        # Scrape ligero (requests primero, Playwright solo si existe)
        if st.button("Scrapear listas (ligero)", use_container_width=True, help="Usa requests y si puede Playwright para refrescar las listas"):
            dataset = _scrape_live(limit_upcoming=40, limit_finished=40)
            source_label = "Scrape en vivo (ligero)"
            st.session_state["live_dataset"] = dataset
        elif "live_dataset" in st.session_state:
            dataset = st.session_state["live_dataset"]
            source_label = "Scrape en vivo (ligero)"

        st.write(f"Fuente: {source_label}")

        st.header("Filtros")
        search = st.text_input("Equipo (contiene)", "")

        handicap_opts = _build_filter_options(
            dataset["upcoming_matches"] + dataset["finished_matches"], "handicap"
        )
        goal_opts = _build_filter_options(
            dataset["upcoming_matches"] + dataset["finished_matches"], "goal_line"
        )
        handicap = st.selectbox("Handicap", handicap_opts, index=0)
        goal_line = st.selectbox("Linea de goles", goal_opts, index=0)

        st.checkbox("Solo partidos futuros", value=True, key="only_future")

        st.header("Analisis por ID (cache)")
        manual_match_id = st.text_input("ID manual", value="", key="manual_match_id_input")
        preview_upload = st.file_uploader("Sube preview JSON (opcional)", type=["json"], key="preview_uploader")
        st.header("Analisis en vivo (requiere navegador)")
        live_match_id = st.text_input("ID a analizar en vivo", value="", key="live_match_id_input")
        run_live = st.button("Analizar en vivo", use_container_width=True, help="Usa Selenium/Playwright segun modules.estudio_scraper")

    upcoming_filtered = _filter_matches(
        dataset["upcoming_matches"], search, handicap, goal_line, st.session_state.get("only_future", True)
    )
    finished_filtered = _filter_matches(
        dataset["finished_matches"], search, handicap, goal_line, False
    )

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Proximos partidos", len(upcoming_filtered))
    with col2:
        st.metric("Partidos finalizados", len(finished_filtered))

    tab1, tab2 = st.tabs(["Proximos", "Finalizados"])
    with tab1:
        _render_list("Proximos partidos", upcoming_filtered)
    with tab2:
        _render_list("Finalizados", finished_filtered)

    if upcoming_filtered or finished_filtered:
        all_rows = []
        for label, items in (("upcoming", upcoming_filtered), ("finished", finished_filtered)):
            for item in items:
                row = dict(item)
                row["section"] = label
                all_rows.append(row)
        df = pd.DataFrame(all_rows)
        st.download_button(
            "Descargar resultado filtrado (CSV)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="matches_filtrados.csv",
            mime="text/csv",
            key="download_filtered",
        )

    # Panel de estudio basado en cache existente
    st.divider()
    st.header("Estudio del partido (usa cache existente)")
    combined = upcoming_filtered + finished_filtered
    options = [f"{m['id']} - {m['home_team']} vs {m['away_team']}" for m in combined]
    match_lookup = {opt: m["id"] for opt, m in zip(options, combined)}

    selected = st.selectbox("Selecciona un partido", options, disabled=not options, placeholder="Elegir de la lista")
    selected_id = match_lookup.get(selected) if selected else None
    manual_id = st.session_state.get("manual_match_id_input", "").strip()
    target_id = selected_id or manual_id

    # Prefer uploaded preview JSON when provided
    preview_data = None
    if preview_upload:
        try:
            preview_data = json.loads(preview_upload.read())
            if not target_id and isinstance(preview_data, dict):
                target_id = str(preview_data.get("match_id") or preview_data.get("id") or "")
        except Exception:
            st.warning("No se pudo leer el preview subido.")

    if not preview_data and target_id:
        preview_data = _load_cached_preview(target_id)

    if not target_id and not preview_data:
        st.info("Selecciona un partido o ingresa un ID en la barra lateral.")
    else:
        _render_preview(preview_data)

    if run_live:
        st.divider()
        st.header("Analisis en vivo")
        if live_match_id.strip():
            _render_live_analysis(live_match_id.strip())
        else:
            st.warning("Introduce un ID para analizar en vivo.")


if __name__ == "__main__":
    main()
