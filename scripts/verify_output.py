#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baloto Oracle — Verificador del artefacto publicado
===================================================
Se ejecuta ANTES del commit/deploy. Falla ruidosamente si:

- data.js no parsea o no expone las cuatro claves esperadas,
- el número de sorteos de data.js no coincide con baloto.json,
- la fecha final de data.js no coincide con metadata.date_range.end,
- algún sorteo tiene números fuera de rango, repetidos o desordenados,
- validation_results.json corresponde a otro dataset.

Sin esto, un data.js corrupto llegaba a producción: el push del bot usa
GITHUB_TOKEN, y GitHub no crea runs de CI para eventos originados por ese token.
"""

import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED = BASE_DIR / "data" / "processed"
DATA_JS = BASE_DIR / "src" / "js" / "data.js"


def fail(msg: str) -> None:
    print(f"FALLO: {msg}")
    sys.exit(1)


def load_json(name: str):
    with open(PROCESSED / name, encoding="utf-8") as fh:
        return json.load(fh)


def extract(data_js: str, key: str):
    """Extrae window.BAL_DATA.<key> = <json>; del script generado."""
    m = re.search(rf"window\.BAL_DATA\.{key} = (.*?);\n", data_js, re.S)
    if not m:
        fail(f"data.js no contiene window.BAL_DATA.{key}")
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        fail(f"window.BAL_DATA.{key} no es JSON válido: {exc}")


def check_draws(draws, game: str) -> None:
    if not draws:
        fail(f"{game}: lista vacía")
    dates = [d["date"] for d in draws]
    if dates != sorted(dates):
        fail(f"{game}: fechas no ordenadas")
    if len(set(dates)) != len(dates):
        fail(f"{game}: fechas duplicadas")
    for d in draws:
        nums = d["numbers"]
        if len(nums) != 5 or len(set(nums)) != 5:
            fail(f"{game} {d['date']}: no son 5 números distintos")
        if nums != sorted(nums):
            fail(f"{game} {d['date']}: números no ordenados")
        if not all(1 <= n <= 43 for n in nums):
            fail(f"{game} {d['date']}: número fuera de 1..43")
        if not 1 <= d["superbalota"] <= 16:
            fail(f"{game} {d['date']}: superbalota fuera de 1..16")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d["date"]):
            fail(f"{game}: fecha con formato inválido: {d['date']}")


def main() -> None:
    if not DATA_JS.exists():
        fail("no existe src/js/data.js")

    baloto = load_json("baloto.json")
    revancha = load_json("revancha.json")
    metadata = load_json("metadata.json")
    analysis = load_json("analysis_results.json")

    check_draws(baloto, "baloto")
    check_draws(revancha, "revancha")

    data_js = DATA_JS.read_text(encoding="utf-8")
    js_baloto = extract(data_js, "baloto")
    js_revancha = extract(data_js, "revancha")
    js_metadata = extract(data_js, "metadata")
    extract(data_js, "analysis_results")

    if len(js_baloto) != len(baloto):
        fail(f"data.js tiene {len(js_baloto)} baloto y baloto.json {len(baloto)}")
    if len(js_revancha) != len(revancha):
        fail(
            f"data.js tiene {len(js_revancha)} revancha y revancha.json {len(revancha)}"
        )
    if js_baloto[-1]["date"] != baloto[-1]["date"]:
        fail("data.js y baloto.json no terminan en la misma fecha")
    if js_metadata["date_range"]["end"] != metadata["date_range"]["end"]:
        fail("metadata de data.js y metadata.json no coinciden")
    if metadata["total_draws"] != len(baloto):
        fail(f"metadata.total_draws={metadata['total_draws']} != {len(baloto)}")
    if analysis["metadata"]["total_draws_analyzed"] != len(baloto):
        fail("analysis_results.json analizó otro dataset")

    try:
        validation = load_json("validation_results.json")
    except FileNotFoundError:
        validation = None
    if validation is not None:
        v_draws = validation.get("data", {}).get("draws")
        if v_draws is not None and v_draws != len(baloto):
            fail(f"validation_results.json tiene {v_draws} sorteos, no {len(baloto)}")

    print(
        f"OK: {len(baloto)} sorteos ({baloto[0]['date']} -> {baloto[-1]['date']}), "
        f"data.js coherente, validación {'presente' if validation else 'ausente'}"
    )


if __name__ == "__main__":
    main()
