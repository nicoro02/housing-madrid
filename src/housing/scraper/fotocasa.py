"""Scraper de prueba para Fotocasa con scroll y dedupe."""
from __future__ import annotations

import random
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from playwright.sync_api import sync_playwright

from ..config import settings
from ..db import get_mongo_db

DEFAULT_SEARCH_URL = (
    "https://www.fotocasa.es/es/comprar/viviendas/madrid-provincia/todas-las-zonas/l"
)
DATA_RAW = Path("data/raw")
DATA_RAW.mkdir(parents=True, exist_ok=True)

CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def _canonical(url: str) -> str:
    """Quita query y fragmento para deduplicar variantes de galeria."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _accept_cookies(page):
    try:
        page.locator("#didomi-notice-agree-button").click(timeout=5000)
        print("[probe] cookies aceptadas")
    except Exception:
        print("[probe] no hubo banner de cookies")


def _scroll_to_load(page, n_scrolls: int = 8):
    """Baja la pagina varias veces para forzar lazy loading."""
    for i in range(n_scrolls):
        page.mouse.wheel(0, 2000)
        page.wait_for_timeout(700)
    print(f"[probe] {n_scrolls} scrolls completados")


def _extract_listing_urls(page) -> list[str]:
    anchors = page.locator("a[href*='/vivienda/']").all()
    seen: set[str] = set()
    for a in anchors:
        href = a.get_attribute("href")
        if not href or "/vivienda/" not in href:
            continue
        if href.startswith("/"):
            href = "https://www.fotocasa.es" + href
        seen.add(_canonical(href))
    return sorted(seen)


def probe(search_url: str = DEFAULT_SEARCH_URL) -> dict:
    delay = random.uniform(settings.scrape_min_delay_sec, settings.scrape_max_delay_sec)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=CHROME_UA, locale="es-ES")
        page = context.new_page()

        print(f"[probe] GET {search_url}")
        page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
        _accept_cookies(page)

        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            print("[probe] no llego a networkidle, sigo")

        _scroll_to_load(page, n_scrolls=8)
        page.wait_for_timeout(int(delay * 1000))

        title = page.title()
        html = page.content()
        blocked = any(
            marker in html.lower()
            for marker in ("cloudflare", "just a moment", "captcha", "denegado")
        )

        urls = _extract_listing_urls(page)

        probe_path = DATA_RAW / "probe_fotocasa.html"
        probe_path.write_text(html, encoding="utf-8")
        print(f"[probe] HTML guardado en {probe_path.resolve()}")

        browser.close()

    record = {
        "source": "fotocasa",
        "search_url": search_url,
        "scraped_at": datetime.now(timezone.utc),
        "title": title,
        "blocked": blocked,
        "n_listings_found": len(urls),
        "listing_urls": urls[:60],
        "html_length": len(html),
    }
    get_mongo_db()["raw_probes"].insert_one(record.copy())
    return record


if __name__ == "__main__":
    result = probe()
    print(
        f"\nResultado:\n"
        f"  bloqueado   = {result['blocked']}\n"
        f"  title       = {result['title']!r}\n"
        f"  html_length = {result['html_length']}\n"
        f"  anuncios    = {result['n_listings_found']}"
    )
    if result["listing_urls"]:
        print("\nPrimeros 10:")
        for u in result["listing_urls"][:10]:
            print(f"  - {u}")