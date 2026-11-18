#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baloto Oracle — Generador de src/js/data.js
===========================================
Embebe data/processed (baloto.json, revancha.json, metadata.json,
analysis_results.json, validation_results.json) en window.BAL_DATA para que la
web no dependa de fetch.

Además:
- Corrige metadata.draw_days: los días de sorteo se DERIVAN de los datos reales
  (los sábados y miércoles cubren todo el período; los lunes solo desde 2025-06),
  en lugar de asumir un calendario fijo.
- Escapa "</" en el JSON embebido: sin eso, un campo de texto con "</script>"
  cerraría el tag y el resto se interpretaría como HTML.
- Actualiza el cache-buster ?v= de index.html con la fecha del último sorteo, de
  modo que un navegador con data.js cacheado no siga sirviendo datos viejos.
- Falla si el validation_results.json no corresponde al dataset actual.
"""

import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED = BASE_DIR / "data" / "processed"
OUT = BASE_DIR / "src" / "js" / "data.js"
INDEX = BASE_DIR / "index.html"

WEEKDAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def load(name: str):
    with open(PROCESSED / name, "r", encoding="utf-8") as fh:
        return json.load(fh)


def dumps_js(obj) -> str:
    """JSON apto para un <script> clásico: escapa el cierre de tag."""
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def fix_draw_days(metadata: dict, baloto: list) -> dict:
    """Deriva los días de sorteo reales y sus rangos desde los datos."""
    by_day: dict[str, list[str]] = defaultdict(list)
    for d in baloto:
        dt = datetime.strptime(d["date"], "%Y-%m-%d")
        by_day[WEEKDAY_NAMES[dt.weekday()]].append(d["date"])

    counts = {k: len(v) for k, v in by_day.items()}
    ranges = {
        k: {"start": min(v), "end": max(v), "count": len(v)} for k, v in by_day.items()
    }
    ordered = sorted(counts.keys(), key=lambda k: WEEKDAY_NAMES.index(k))
    metadata["draw_days"] = ordered
    metadata["draw_day_ranges"] = ranges
    return metadata


def asset_version() -> str:
    """Cache-buster por CONTENIDO, no por fecha del dato.

    Con `?v=<fecha del sorteo>` un arreglo de CSS/JS no cambiaba la URL: el
    navegador seguía usando el asset viejo y el layout se rompía hasta que
    expirara el caché. Con el hash, cualquier cambio en estos ficheros cambia
    la query.
    """
    digest = hashlib.sha256()
    for rel in ("src/css/main.css", "src/js/main.js", "src/js/data.js"):
        path = BASE_DIR / rel
        if path.exists():
            digest.update(path.read_bytes())
    return digest.hexdigest()[:8]


def update_cache_buster(version: str) -> None:
    """?v= de los assets = hash del contenido de CSS + JS."""
    if not INDEX.exists():
        return
    html = INDEX.read_text(encoding="utf-8")
    new_html = re.sub(r"(src/(?:js|css)/[\w.-]+)\?v=[\w.-]+", rf"\1?v={version}", html)
    if new_html != html:
        INDEX.write_text(new_html, encoding="utf-8")


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

    # El artefacto es determinista: la fecha sale del dato, no del reloj.
    metadata["data_date"] = metadata["date_range"]["end"]

    # La validación debe corresponder al mismo dataset que el análisis.
    if validation is not None:
        v_draws = validation.get("data", {}).get("draws")
        if v_draws is not None and v_draws != len(baloto):
            raise SystemExit(
                f"validation_results.json tiene {v_draws} sorteos y baloto.json "
                f"{len(baloto)}: re-ejecuta scripts/validate_baloto.py"
            )

    with open(PROCESSED / "metadata.json", "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, ensure_ascii=False, indent=2)

    header = (
        "// Datos embebidos - generados desde data/processed para eliminar dependencia de fetch\n"
        f"// Generado para el sorteo del {metadata['data_date']}\n"
        "(function () {\n"
        "  window.BAL_DATA = {};\n"
    )
    body = (
        f"  window.BAL_DATA.baloto = {dumps_js(baloto)};\n"
        f"  window.BAL_DATA.revancha = {dumps_js(revancha)};\n"
        f"  window.BAL_DATA.metadata = {dumps_js(metadata)};\n"
        f"  window.BAL_DATA.analysis_results = {dumps_js(analysis)};\n"
    )
    if validation is not None:
        body += f"  window.BAL_DATA.validation = {dumps_js(validation)};\n"
    footer = "})();\n"

    tmp = OUT.with_suffix(".js.tmp")
    tmp.write_text(header + body + footer, encoding="utf-8")
    tmp.replace(OUT)

    version = asset_version()
    update_cache_buster(version)

    print(
        f"data.js escrito: {len(baloto)} baloto, {len(revancha)} revancha, "
        f"{OUT.stat().st_size} bytes | draw_days={metadata['draw_days']}"
    )
    print(
        f"draw_day_ranges={json.dumps(metadata['draw_day_ranges'], ensure_ascii=False)}"
    )
    print(f"cache-buster aplicado: ?v={version}")


if __name__ == "__main__":
    main()
