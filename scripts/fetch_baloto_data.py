#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baloto Oracle — Data Fetcher (DATOS REALES)
===========================================
Extrae el historial oficial de resultados de Baloto y Revancha desde el sitio
oficial: https://www.baloto.com/resultados?page=1..125

- NO genera datos sintéticos (se eliminó create_sample_data).
- NO depende de Kaggle (se eliminó download_kaggle_dataset).
- Cada página oficial contiene 10 filas: 5 sorteos Baloto + 5 Revancha.
- La última página (125) llega hasta el 1 de Mayo de 2021.
- El jackpot se obtiene de la página de detalle del sorteo más reciente
  (texto "ACUMULADO DEL SORTEO: $XX.XXX MILLONES"); el resto queda null.

Salida:
  data/raw/baloto_historical.csv        (draw_id,date,numbers,superbalota,jackpot,game)
  data/raw/revancha_historical.csv      (ídem)
  data/processed/baloto.json            (array de sorteos)
  data/processed/revancha.json          (array de sorteos)
  data/processed/metadata.json          (source, total_draws, date_range, ...)
"""

import csv
import json
import logging
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("fetch_baloto")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"

OFFICIAL_RESULTS_URL = "https://www.baloto.com/resultados"
OFFICIAL_DETAIL_URL = "https://www.baloto.com/resultados-baloto/{draw_id}"
MAX_PAGES = 125
REQUEST_DELAY = 0.8  # segundos entre peticiones (cortesía)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Accept-Language": "es-CO,es;q=0.9",
}

SPANISH_MONTHS = {
    "Enero": 1,
    "Febrero": 2,
    "Marzo": 3,
    "Abril": 4,
    "Mayo": 5,
    "Junio": 6,
    "Julio": 7,
    "Agosto": 8,
    "Septiembre": 9,
    "Octubre": 10,
    "Noviembre": 11,
    "Diciembre": 12,
}

JACKPOT_RE = re.compile(
    r"ACUMULADO\s+DEL\s+SORTEO:\s*\$?\s*([\d.,]+)\s*MILLONES", re.IGNORECASE
)


def parse_spanish_date(text: str) -> str | None:
    """'26 de Agosto de 2026' -> '2026-08-26'. Devuelve None si no parsea."""
    m = re.match(r"(\d{1,2})\s+de\s+([A-Za-z]+)\s+de\s+(\d{4})", text.strip())
    if not m:
        return None
    day, month_name, year = m.groups()
    month = SPANISH_MONTHS.get(month_name)
    if month is None:
        return None
    return f"{year}-{month:02d}-{int(day):02d}"


def fetch_page(session: requests.Session, page: int) -> str | None:
    """Descarga una página de resultados con reintentos. None si falla todo."""
    url = f"{OFFICIAL_RESULTS_URL}?page={page}"
    for attempt in range(3):
        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as exc:
            logger.warning("page %s intento %s falló: %s", page, attempt + 1, exc)
            time.sleep(2 * (attempt + 1))
    return None


def parse_results_page(html: str) -> list[dict]:
    """Extrae (game, date_iso, numbers, superbalota) de la tabla oficial."""
    soup = BeautifulSoup(html, "lxml")
    rows = soup.select("table#results-table tbody tr")
    draws: list[dict] = []
    for tr in rows:
        img = tr.select_one("td img")
        if img is None:
            continue
        src = img.get("src", "")
        if "baloto-kind.png" in src:
            game = "Baloto"
        elif "revancha-kind.png" in src:
            game = "Revancha"
        else:
            continue

        date_td = tr.select_one("td.creation-date-results")
        date_iso = parse_spanish_date(date_td.get_text(strip=True)) if date_td else None
        if date_iso is None:
            logger.warning(
                "fila sin fecha parseable: %s", tr.get_text(" ", strip=True)[:80]
            )
            continue

        # El resultado vive en el td con clase style-* (5 números + superbalota)
        result_td = tr.select_one('td[class*="style-"]')
        if result_td is None:
            continue
        tokens = [
            t.strip()
            for t in re.split(r"\s*-\s*", result_td.get_text(" ", strip=True))
            if t.strip()
        ]
        if len(tokens) < 6:
            continue
        try:
            numbers = [int(t) for t in tokens[:5]]
            superbalota = int(tokens[5])
        except ValueError:
            logger.warning("números no parseables: %s", tokens)
            continue
        if not all(1 <= n <= 43 for n in numbers) or not (1 <= superbalota <= 16):
            continue

        # Identificador oficial del sorteo (href del enlace "Ver detalle")
        official_id = None
        detail_link = tr.select_one("a[href*='/resultados-']")
        if detail_link is not None:
            m = re.search(r"/(\d+)$", detail_link.get("href", ""))
            if m:
                official_id = int(m.group(1))

        draws.append(
            {
                "game": game,
                "date": date_iso,
                "numbers": numbers,
                "superbalota": superbalota,
                "official_id": official_id,
            }
        )
    return draws


def fetch_current_jackpot(session: requests.Session, draw_id: int) -> int | None:
    """Jackpot real del sorteo más reciente desde su página de detalle."""
    url = OFFICIAL_DETAIL_URL.format(draw_id=draw_id)
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("detalle jackpot falló: %s", exc)
        return None
    m = JACKPOT_RE.search(resp.text)
    if not m:
        return None
    try:
        millones = float(m.group(1).replace(".", "").replace(",", "."))
        return int(millones * 1_000_000)
    except ValueError:
        return None


def scrape_all(session: requests.Session) -> tuple[list[dict], list[dict]]:
    """Itera páginas 1..MAX_PAGES. Detiene si una página no aporta filas nuevas."""
    baloto: list[dict] = []
    revancha: list[dict] = []
    seen: set[tuple] = set()

    for page in range(1, MAX_PAGES + 1):
        html = fetch_page(session, page)
        if html is None:
            logger.error("abortando en page %s (descarga fallida)", page)
            break
        rows = parse_results_page(html)
        if not rows:
            logger.info("page %s sin filas — fin del historial", page)
            break

        new_rows = 0
        for row in rows:
            key = (row["game"], row["date"], tuple(row["numbers"]), row["superbalota"])
            if key in seen:
                continue
            seen.add(key)
            new_rows += 1
            (baloto if row["game"] == "Baloto" else revancha).append(row)

        logger.info("page %s: %s filas (%s nuevas)", page, len(rows), new_rows)
        if new_rows == 0:
            logger.info("page %s duplicada — fin del historial", page)
            break
        time.sleep(REQUEST_DELAY)

    return baloto, revancha


def to_csv(draws: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["draw_id", "date", "numbers", "superbalota", "jackpot", "game"]
        )
        for i, d in enumerate(draws, start=1):
            writer.writerow(
                [
                    i,
                    d["date"],
                    json.dumps(d["numbers"]),
                    d["superbalota"],
                    d.get("jackpot"),
                    d["game"],
                ]
            )


def to_json(draws: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(draws, fh, ensure_ascii=False)


def write_metadata(
    baloto: list[dict], revancha: list[dict], current_jackpot: int | None
) -> None:
    start = min(d["date"] for d in baloto)
    end = max(d["date"] for d in baloto)
    metadata = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_draws": len(baloto),
        "date_range": {"start": start, "end": end},
        "games": ["Baloto", "Revancha"],
        "format": "5/43 + 1/16 (Superbalota)",
        "draw_days": ["Monday", "Wednesday", "Saturday"],
        "draw_time": "23:00 COT",
        "source": (
            "https://www.baloto.com/resultados (sitio oficial — scraping "
            "paginado, páginas 1..125, sin datos sintéticos)"
        ),
        "current_jackpot": current_jackpot,
    }
    with open(DATA_PROCESSED / "metadata.json", "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, ensure_ascii=False, indent=2)
    logger.info("metadata.json escrito: %s sorteos, %s → %s", len(baloto), start, end)


def run() -> None:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update(HEADERS)

    logger.info("Scraping oficial %s?page=1..%s", OFFICIAL_RESULTS_URL, MAX_PAGES)
    baloto, revancha = scrape_all(session)

    if not baloto:
        logger.error("no se obtuvieron datos — abortando")
        sys.exit(1)

    # El sorteo más reciente es la primera fila de la página 1.
    baloto_sorted = sorted(baloto, key=lambda d: d["date"], reverse=True)
    current_jackpot = None
    if baloto_sorted:
        latest_official_id = baloto_sorted[0].get("official_id")
        current_jackpot = fetch_current_jackpot(session, latest_official_id or 1)

    # Asignar jackpot solo al sorteo más reciente; el resto queda null.
    if current_jackpot is not None and baloto_sorted:
        baloto_sorted[0]["jackpot"] = current_jackpot

    # Descartar official_id (no forma parte del contrato de datos de la web).
    for d in baloto + revancha:
        d.pop("official_id", None)

    # Orden cronológico ascendente (coherente con la versión previa y con data.js).
    baloto.sort(key=lambda d: d["date"])
    revancha.sort(key=lambda d: d["date"])

    to_csv(baloto, DATA_RAW / "baloto_historical.csv")
    to_csv(revancha, DATA_RAW / "revancha_historical.csv")
    to_json(baloto, DATA_PROCESSED / "baloto.json")
    to_json(revancha, DATA_PROCESSED / "revancha.json")
    write_metadata(baloto, revancha, current_jackpot)

    logger.info(
        "OK: %s Baloto (%s → %s), %s Revancha (%s → %s), jackpot actual=%s",
        len(baloto),
        baloto[0]["date"],
        baloto[-1]["date"],
        len(revancha),
        revancha[0]["date"],
        revancha[-1]["date"],
        current_jackpot,
    )


if __name__ == "__main__":
    run()
