#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests del pipeline de datos.

Cubren lo que puede romperse en silencio: el parseo del sitio oficial y la
integridad del contrato que consume la web. Se ejecutan con `pytest scripts/`.
"""

import json
import sys
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

import fetch_baloto_data as fetch  # noqa: E402

PROCESSED = BASE_DIR / "data" / "processed"


# --------------------------- parseo del sitio ------------------------------
def test_parse_spanish_date():
    assert fetch.parse_spanish_date("26 de Agosto de 2026") == "2026-08-26"
    assert fetch.parse_spanish_date("1 de mayo de 2021") == "2021-05-01"
    assert fetch.parse_spanish_date("texto sin fecha") is None
    assert fetch.parse_spanish_date("32 de Agosto de 2026") is None


def test_parse_spanish_date_rejects_unknown_month():
    assert fetch.parse_spanish_date("5 de Smarch de 2026") is None


def test_jackpot_regex():
    m = fetch.JACKPOT_RE.search("ACUMULADO DEL SORTEO: $55.600 MILLONES")
    assert m is not None
    assert float(m.group(1).replace(".", "").replace(",", ".")) == 55600


def test_parse_results_page_ignores_garbage():
    html = """
    <table id="results-table"><tbody>
      <tr><td><img src="baloto-kind.png"></td>
          <td class="creation-date-results">26 de Agosto de 2026</td>
          <td class="style-1">1 - 2 - 3 - 4 - 5 - 6</td></tr>
      <tr><td><img src="baloto-kind.png"></td>
          <td class="creation-date-results">sin fecha</td>
          <td class="style-1">1 - 2 - 3 - 4 - 5 - 6</td></tr>
      <tr><td><img src="otro.png"></td>
          <td class="creation-date-results">27 de Agosto de 2026</td>
          <td class="style-1">1 - 2 - 3 - 4 - 5 - 6</td></tr>
    </tbody></table>
    """
    rows = fetch.parse_results_page(html)
    assert len(rows) == 1
    assert rows[0]["numbers"] == [1, 2, 3, 4, 5]
    assert rows[0]["superbalota"] == 6


def test_parse_results_page_rejects_out_of_range():
    html = """
    <table id="results-table"><tbody>
      <tr><td><img src="revancha-kind.png"></td>
          <td class="creation-date-results">26 de Agosto de 2026</td>
          <td class="style-1">1 - 2 - 3 - 4 - 44 - 6</td></tr>
    </tbody></table>
    """
    assert fetch.parse_results_page(html) == []


# --------------------------- contrato de datos -----------------------------
@pytest.mark.parametrize("game", ["baloto", "revancha"])
def test_processed_draws_are_valid(game):
    path = PROCESSED / f"{game}.json"
    if not path.exists():
        pytest.skip(f"{game}.json no generado")
    draws = json.loads(path.read_text(encoding="utf-8"))
    assert draws, f"{game}.json vacío"
    dates = [d["date"] for d in draws]
    assert dates == sorted(dates), "fechas desordenadas"
    assert len(set(dates)) == len(dates), "fechas duplicadas"
    for d in draws:
        assert len(d["numbers"]) == 5
        assert len(set(d["numbers"])) == 5
        assert d["numbers"] == sorted(d["numbers"])
        assert all(1 <= n <= 43 for n in d["numbers"])
        assert 1 <= d["superbalota"] <= 16


def test_metadata_matches_draws():
    meta = json.loads((PROCESSED / "metadata.json").read_text(encoding="utf-8"))
    draws = json.loads((PROCESSED / "baloto.json").read_text(encoding="utf-8"))
    assert meta["total_draws"] == len(draws)
    assert meta["date_range"]["start"] == draws[0]["date"]
    assert meta["date_range"]["end"] == draws[-1]["date"]


def test_merge_never_loses_history():
    existing = [
        {"date": "2021-05-01", "numbers": [1, 2, 3, 4, 5], "superbalota": 1},
        {"date": "2021-05-05", "numbers": [1, 2, 3, 4, 6], "superbalota": 2},
    ]
    # Un scrape parcial que solo trae el sorteo más reciente
    scraped = [{"date": "2026-11-16", "numbers": [7, 8, 9, 10, 11], "superbalota": 3}]
    merged = fetch.merge_draws(existing, scraped)
    assert len(merged) == 3
    assert merged[0]["date"] == "2021-05-01"
    assert merged[-1]["date"] == "2026-11-16"


def test_merge_scrape_wins_on_same_date():
    existing = [{"date": "2021-05-01", "numbers": [1, 2, 3, 4, 5], "superbalota": 1}]
    scraped = [{"date": "2021-05-01", "numbers": [9, 9, 9, 9, 9], "superbalota": 9}]
    assert fetch.merge_draws(existing, scraped)[0]["numbers"] == [9, 9, 9, 9, 9]


# --------------------------- análisis publicados ---------------------------
def test_predictions_sum_to_five():
    path = PROCESSED / "analysis_results.json"
    if not path.exists():
        pytest.skip("analysis_results.json no generado")
    analysis = json.loads(path.read_text(encoding="utf-8"))
    probs = analysis["predictions"]["next_draw_numbers"]["probabilities"]
    assert len(probs) == 43
    assert abs(sum(probs.values()) - 5) < 1e-6
    top5 = analysis["predictions"]["next_draw_numbers"]["top_5_most_likely"]
    ordered = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
    assert top5 == [int(k) for k, _ in ordered[:5]]


def test_position_test_has_no_tautological_result():
    """Kruskal-Wallis sobre posiciones ordenadas rechazaba siempre (p=0)."""
    path = PROCESSED / "analysis_results.json"
    if not path.exists():
        pytest.skip("analysis_results.json no generado")
    analysis = json.loads(path.read_text(encoding="utf-8"))
    pos = analysis["inferential"]["non_parametric"]["kruskal_wallis_position"]
    assert "per_position" in pos
    assert pos["methodology"].startswith("Cada posición")
