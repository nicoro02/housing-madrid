"""Crawler paginado de Fotocasa: recorre N paginas y guarda URLs en Mongo."""
from __future__ import annotations

import random
import sys
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit

from playwright.sync_api import sync_playwright

from ..config import settings
from ..db import get_mongo_db

BASE_URL = (
    "https://www.fotocasa.es/es/comprar/viviendas/madrid-provincia/todas-las-zonas/l"
)
CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def _canonical(url: str) -> str:
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc, p.path, "", ""))


def _accept_cookies(page):
    try:
        page.locator("#didomi-notice-agree-button").click(timeout=5000)
    except Exception:
        pass


def _scroll(page, n=12):
    for _ in range(n):
        page.mouse.wheel(0, 2500)
        page.wait_for_timeout(600)


def _extract_urls(page) -> set[str]:
    anchors = page.locator("a[href*='/vivienda/']").all()
    urls: set[str] = set()
    for a in anchors:
        href = a.get_attribute("href")
        if not href or "/vivienda/" not in href:
            continue
        if href.startswith("/"):
            href = "https://www.fotocasa.es" + href
        urls.add(_canonical(href))
    return urls


def crawl(max_pages: int = 20) -> dict:
    all_urls: set[str] = set()
    per_page: list[int] = []
    empty_streak = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(user_agent=CHROME_UA, locale="es-ES")
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()

        for page_n in range(1, max_pages + 1):
            url = BASE_URL if page_n == 1 else f"{BASE_URL}/{page_n}"
            print(f"[crawl] pagina {page_n}/{max_pages}: {url}")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(3000)
            except Exception as e:
                print(f"[crawl]   error goto: {e}")
                continue

            if page_n == 1:
                _accept_cookies(page)

            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass

            _scroll(page, n=12)
            new_urls = _extract_urls(page)
            per_page.append(len(new_urls))
            before = len(all_urls)
            all_urls.update(new_urls)
            added = len(all_urls) - before
            print(
                f"[crawl]   {len(new_urls)} en pagina, +{added} nuevas, total unicos: {len(all_urls)}"
            )
            if added == 0:
                empty_streak += 1
                if empty_streak >= 3:
                    print("[crawl] 3 paginas seguidas sin URLs nuevas, corto aqui")
                    break
            else:
                empty_streak = 0

            delay = random.uniform(
                settings.scrape_min_delay_sec, settings.scrape_max_delay_sec
            )
            page.wait_for_timeout(int(delay * 1000))

        browser.close()

    db = get_mongo_db()
    coll = db["listings_urls"]
    coll.create_index("url", unique=True)
    now = datetime.now(timezone.utc)
    inserted = 0
    for url in all_urls:
        r = coll.update_one(
            {"url": url},
            {"$setOnInsert": {"url": url, "source": "fotocasa", "discovered_at": now}},
            upsert=True,
        )
        if r.upserted_id is not None:
            inserted += 1

    return {
        "pages_crawled": len(per_page),
        "total_unique_urls": len(all_urls),
        "urls_per_page": per_page,
        "new_urls_inserted": inserted,
    }


if __name__ == "__main__":
    max_pages = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    print(f"[crawl] arrancando: max_pages={max_pages}")
    result = crawl(max_pages=max_pages)
    print("\nResultado:")
    print(f"  paginas recorridas   = {result['pages_crawled']}")
    print(f"  URLs unicas totales  = {result['total_unique_urls']}")
    print(f"  URLs nuevas en Mongo = {result['new_urls_inserted']}")
    print(f"  URLs por pagina      = {result['urls_per_page']}")