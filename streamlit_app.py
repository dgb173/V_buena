"""
Streamlit viewer for scraped match data.

The app reads a `data.json` file (either uploaded by the user or already
present in the repo) and renders upcoming/finished matches with basic
filters. No Playwright or Selenium is used here so it can run safely on
Render's Streamlit runtime.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st


DEFAULT_DATA_PATHS = [
    Path("data.json"),
    Path("src/data.json"),
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


def _build_filter_options(matches: List[Dict[str, Any]], field: str) -> List[str]:
    values = sorted({str(m.get(field)) for m in matches if m.get(field) not in (None, "", "N/A")})
    return ["(Todos)"] + values


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


if __name__ == "__main__":
    main()
