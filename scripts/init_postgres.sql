-- Esquema curated de referencia. Se irá refinando conforme avancemos.

CREATE SCHEMA IF NOT EXISTS curated;

CREATE TABLE IF NOT EXISTS curated.listings (
    id              TEXT PRIMARY KEY,
    source          TEXT NOT NULL,
    scraped_at      TIMESTAMP NOT NULL,
    url             TEXT NOT NULL,

    price_eur       NUMERIC(12,2),
    surface_m2      NUMERIC(8,2),
    rooms           INTEGER,
    bathrooms       INTEGER,
    floor           TEXT,
    property_type   TEXT,
    condition       TEXT,
    build_year      INTEGER,
    has_lift        BOOLEAN,
    has_ac          BOOLEAN,
    has_parking     BOOLEAN,
    has_terrace     BOOLEAN,

    municipality    TEXT,
    district        TEXT,
    neighborhood    TEXT,
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION,

    metro_distance_m NUMERIC(8,2),
    poi_score        NUMERIC(6,3)
);

CREATE INDEX IF NOT EXISTS ix_listings_municipality ON curated.listings (municipality);
CREATE INDEX IF NOT EXISTS ix_listings_price ON curated.listings (price_eur);
