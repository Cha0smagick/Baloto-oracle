#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baloto Oracle — Generador de src/js/data.js
===========================================
Embebe data/processed (baloto.json, revancha.json, metadata.json,
analysis_results.json) en window.BAL_DATA para que la web no dependa de fetch.

Además corrige metadata.draw_days: los días de sorteo se DERIVAN de los datos
reales (los sábados y miércoles cubren todo el período; los lunes solo desde
2025-05), en lugar de asumir un calendario fijo.
"""

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED = BASE_DIR / "data" / "processed"
OUT = BASE_DIR / "src" / "js" / "data.js"

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def load(name: str):
    with open(PROCESSED / name, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fix_draw_days(metadata: dict, baloto: list) -> dict:
    """Deriva los días de sorteo reales y sus rangos desde los datos."""
    by_day: dict[str, list[str]] = defaultdict(list)
    for d in baloto:
        dt = datetime.strptime(d["date"], "%Y-%m-%d")
        by_day[WEEKDAY_NAMES[dt.weekday()]].append(d["date"])

    counts = {k: len(v) for k, v in by_day.items()}
    ranges = {k: {"start": min(v), "end": max(v), "count": len(v)} for k, v in by_day.items()}
    ordered = sorted(counts.keys(), key=lambda k: WEEKDAY_NAMES.index(k))
    metadata["draw_days"] = ordered
    metadata["draw_day_ranges"] = ranges
    return metadata


def main() -> None:
    baloto = load("baloto.json")
    revancha = load("revancha.json")
    metadata = load("metadata.json")
    analysis = load("analysis_results.json")
    try:
        validation = load("validation_results.json")
    except FileNotFoundError:
        validation = None

    fix_draw_days(metadata, baloto)

    with open(PROCESSED / "metadata.json", "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, ensure_ascii=False, indent=2)

    header = (
        "// Datos embebidos - generados desde data/processed para eliminar dependencia de fetch\n"
        f"// Generado: {datetime.now(timezone.utc).isoformat()}\n"
        "(function () {\n"
        "  window.BAL_DATA = {};\n"
    )
    body = (
        f"  window.BAL_DATA.baloto = {json.dumps(baloto, ensure_ascii=False)};\n"
        f"  window.BAL_DATA.revancha = {json.dumps(revancha, ensure_ascii=False)};\n"
        f"  window.BAL_DATA.metadata = {json.dumps(metadata, ensure_ascii=False)};\n"
        f"  window.BAL_DATA.analysis_results = {json.dumps(analysis, ensure_ascii=False)};\n"
    )
    if validation is not None:
        body += f"  window.BAL_DATA.validation = {json.dumps(validation, ensure_ascii=False)};\n"
    footer = "})();\n"

    OUT.write_text(header + body + footer, encoding="utf-8")
    print(
        f"data.js escrito: {len(baloto)} baloto, {len(revancha)} revancha, "
        f"{OUT.stat().st_size} bytes | draw_days={metadata['draw_days']}"
    )
    print(f"draw_day_ranges={json.dumps(metadata['draw_day_ranges'], ensure_ascii=False)}")


if __name__ == "__main__":
    main()