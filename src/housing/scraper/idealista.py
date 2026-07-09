"""Scraper de prueba para Idealista con Playwright."""
from __future__ import annotations

import random
import sys
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

from ..config import settings
from ..db import get_mongo_db

DEFAULT_SEARCH_URL = "https://www.idealista.com/venta-viviendas/madrid-madrid/"
DATA_RAW = Path("data/raw")
DATA_RAW.mkdir(parents=True, exist_ok=True)


def _extract_listing_urls(page) -> list[str]:
    candidates = [
        "a.item-link",
        "article[data-adid] a[href*='/inmueble/']",
        "a[href*='/inmueble/']",
        "article a[href*='/inmueble/']",
    ]
    seen: set[str] = set()
    for selector in candidates:
        try:
            anchors = page.locator(selector).all()
        except Exception:
            continue
        for a in anchors:
            href = a.get_attribute("href")
            if not href:
                continue
            if "/inmueble/" in href:
                seen.add(href)
        if seen:
            print(f"[probe] selector que funciono: {selector} -> {len(seen)} URLs")
            break
    return sorted(seen)


def probe(search_url: str = DEFAULT_SEARCH_URL) -> dict:
    delay = random.uniform(settings.scrape_min_delay_sec, settings.scrape_max_delay_sec)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=settings.scrape_user_agent, locale="es-ES")
        page = context.new_page()

        print(f"[probe] GET {search_url}")
        page.goto(search_url, wait_until="domcontentloaded", timeout=45000)

        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            print("[probe] no llego a networkidle en 15s, sigo con lo que hay")

        page.wait_for_timeout(int(delay * 1000))

        title = page.title()
        html = page.content()
        blocked = any(
            marker in html.lower()
            for marker in ("cloudflare", "just a moment", "checking your browser", "captcha")
        )

        urls = _extract_listing_urls(page)

        probe_html_path = DATA_RAW / "probe.html"
        probe_html_path.write_text(html, encoding="utf-8")
        print(f"[probe] HTML guardado en {probe_html_path.resolve()}")

        final_url = page.url
        has_cookie_banner = bool(page.locator("#didomi-notice, #onetrust-banner-sdk").count())

        browser.close()

    record = {
        "source": "idealista",
        "search_url": search_url,
        "final_url": final_url,
        "scraped_at": datetime.now(timezone.utc),
        "title": title,
        "blocked": blocked,
        "has_cookie_banner": has_cookie_banner,
        "n_listings_found": len(urls),
        "listing_urls": urls[:30],
        "html_length": len(html),
    }

    db = get_mongo_db()
    db["raw_probes"].insert_one(record.copy())

    return record


if __name__ == "__main__":
    result = probe()
    print(
        f"\nResultado:\n"
        f"  bloqueado           = {result['blocked']}\n"
        f"  cookie_banner       = {result['has_cookie_banner']}\n"
        f"  title               = {result['title']!r}\n"
        f"  final_url           = {result['final_url']}\n"
        f"  html_length         = {result['html_length']} chars\n"
        f"  anuncios_encontrados = {result['n_listings_found']}"
    )
    if result["listing_urls"]:
        print("\nPrimeros 5 anuncios:")
        for u in result["listing_urls"][:5]:
            print(f"  - {u}")
    else:
        print(
            "\nSin anuncios. Revisa data/raw/probe.html en el navegador para ver"
            " que te esta sirviendo Idealista realmente."
        )