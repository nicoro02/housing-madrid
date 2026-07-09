"""Scraper de detalle para Fotocasa. Extrae datos del JSON embebido."""
from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright

from ..config import settings
from ..db import get_mongo_db

CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def _accept_cookies(page):
    try:
        page.locator("#didomi-notice-agree-button").click(timeout=5000)
    except Exception:
        pass


def _extract_initial_props(page) -> dict | None:
    try:
        script = page.locator("script#__initial_props__").first
        content = script.text_content(timeout=3000)
        if not content:
            return None
        return json.loads(content)
    except Exception:
        return None


def _extract_fields(props: dict) -> dict:
    entity = props.get("realEstateAdDetailEntityV2", {}) or {}
    realestate = props.get("realEstate", {}) or {}
    address = entity.get("address", {}) or {}
    coordinates = address.get("coordinates", {}) or {}
    street = address.get("street", {}) or {}
    price = entity.get("price", {}) or {}
    publisher = entity.get("publisher", {}) or {}
    features = realestate.get("features", {}) or {}
    energy = entity.get("energyCertificate", {}) or {}

    features_map = {}
    for f in entity.get("features", []) or []:
        if isinstance(f, dict) and "type" in f:
            features_map[f["type"]] = f.get("value")

    return {
        "property_id": entity.get("propertyId") or realestate.get("id"),
        "property_type_id": entity.get("propertyTypeId"),
        "property_subtype_id": entity.get("propertySubtypeId"),
        "transaction_type_id": entity.get("transactionTypeId"),
        "construction_type": entity.get("constructionType"),
        "creation_date": entity.get("creationDate"),
        "price_eur": price.get("amount"),
        "price_periodicity": price.get("periodicity"),
        "province": address.get("province"),
        "municipality": address.get("municipality"),
        "locality": address.get("locality"),
        "district": address.get("district"),
        "neighborhood": address.get("neighborhood"),
        "zip_code": address.get("zipCode"),
        "street_name": street.get("name"),
        "street_number": street.get("number"),
        "latitude": coordinates.get("lat"),
        "longitude": coordinates.get("lng"),
        "location_is_exact": address.get("isExact"),
        "surface_m2": features.get("surface"),
        "surface_land_m2": features.get("surfaceLand"),
        "rooms": features.get("rooms"),
        "bathrooms": features.get("bathrooms"),
        "floor": features_map.get("FLOOR"),
        "orientation": features_map.get("ORIENTATION"),
        "antiquity": features_map.get("ANTIQUITY"),
        "typology": features_map.get("TYPOLOGY"),
        "elevator": features_map.get("ELEVATOR"),
        "furnished": features_map.get("FURNISHED"),
        "hot_water": features_map.get("HOT_WATER"),
        "heating": features_map.get("HEATING"),
        "occupancy_status": features_map.get("OCCUPANCY_STATUS"),
        "extra_features": entity.get("extraFeatures", []),
        "energy_efficiency_rating": energy.get("energyEfficiencyRatingType"),
        "energy_efficiency_value": energy.get("energyEfficiency"),
        "environment_impact_rating": energy.get("environmentImpactRatingType"),
        "environment_impact_value": energy.get("environmentImpact"),
        "publisher_id": publisher.get("id"),
        "publisher_name": publisher.get("name"),
        "publisher_alias": publisher.get("alias"),
        "publisher_type": publisher.get("type"),
        "reference": publisher.get("reference"),
        "description": entity.get("description"),
        "title": props.get("propertyTitle"),
    }


def scrape_detail(page, url: str) -> dict:
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(2500)
    html = page.content()
    blocked = any(
        m in html.lower() for m in ("cloudflare", "just a moment", "captcha", "denegado")
    )
    if blocked:
        return {"url": url, "scraped_at": datetime.now(timezone.utc), "blocked": True}

    props = _extract_initial_props(page)
    if not props:
        return {
            "url": url,
            "scraped_at": datetime.now(timezone.utc),
            "blocked": False,
            "error": "no se encontro __initial_props__",
        }

    fields = _extract_fields(props)
    fields["url"] = url
    fields["scraped_at"] = datetime.now(timezone.utc)
    fields["blocked"] = False
    return fields


def run(n_urls: int = 5) -> None:
    db = get_mongo_db()
    urls_coll = db["listings_urls"]
    details_coll = db["listings_raw"]
    details_coll.create_index("url", unique=True)

    already = set(d["url"] for d in details_coll.find({}, {"url": 1}))
    all_urls = [d["url"] for d in urls_coll.find({}, {"url": 1})]
    urls = [u for u in all_urls if u not in already][:n_urls]

    if not urls:
        print("[detail] no hay URLs pendientes por scrapear")
        return

    print(f"[detail] procesando {len(urls)} URLs")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(user_agent=CHROME_UA, locale="es-ES")
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = context.new_page()

        page.goto("https://www.fotocasa.es", wait_until="domcontentloaded", timeout=45000)
        _accept_cookies(page)
        page.wait_for_timeout(1500)

        for i, url in enumerate(urls, 1):
            print(f"\n[detail] {i}/{len(urls)}: {url}")
            try:
                result = scrape_detail(page, url)
            except Exception as e:
                print(f"[detail]   ERROR: {e}")
                continue

            if result.get("blocked"):
                print("[detail]   BLOQUEADO")
            elif result.get("error"):
                print(f"[detail]   {result['error']}")
            else:
                print(
                    f"[detail]   OK  {result.get('price_eur')}EUR  "
                    f"{result.get('surface_m2')}m2  "
                    f"{result.get('rooms')}h/{result.get('bathrooms')}b  "
                    f"{result.get('municipality')}, {result.get('neighborhood')}"
                )

            details_coll.replace_one({"url": url}, result, upsert=True)

            delay = random.uniform(
                settings.scrape_min_delay_sec, settings.scrape_max_delay_sec
            )
            page.wait_for_timeout(int(delay * 1000))

        browser.close()


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    run(n_urls=n)