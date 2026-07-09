# Housing Madrid: Price Predictor with Confidence Intervals

Predicción de precio de vivienda en la Comunidad de Madrid con intervalos de confianza calibrados. Proyecto end to end de portfolio: scraping propio (Idealista y Fotocasa), doble almacén (MongoDB raw + PostgreSQL curated), modelo con XGBoost más quantile / conformal prediction, tracking con MLflow, servicio en FastAPI dockerizado y deploy en GCP Cloud Run.

*Portfolio project for Data Scientist junior role. Not for commercial use.*

---

## Objetivo

Dada la ficha de una vivienda (m², habitaciones, ubicación, estado, etc.), predecir el precio con un intervalo de confianza al 90%. Salida esperada:

    { "point": 285000, "lower": 265000, "upper": 315000, "coverage_level": 0.9 }

El foco no es solo predecir un valor, es cuantificar la incertidumbre de manera calibrada: el 90% de los intervalos deberían contener el precio real.

## Arquitectura

    scraping (Playwright)  --->  MongoDB (raw)
                                       |
                                       v
                                  ETL / cleaning
                                       |
                                       v
                           PostgreSQL (curated) + POIs (OSM)
                                       |
                                       v
                       modelo (XGBoost + conformal) + MLflow
                                       |
                                       v
                           FastAPI + Docker + Cloud Run

## Estructura

    housing-madrid/
    |-- docker-compose.yml          Mongo + Postgres + MLflow
    |-- .env.example                Variables de entorno de referencia
    |-- requirements.txt            Dependencias Python
    |-- Makefile                    Comandos comunes
    |-- scripts/init_postgres.sql   Esquema curated
    |-- src/housing/
    |   |-- config.py               Settings
    |   |-- db.py                   Helpers de conexión
    |   |-- scraper/                Playwright + parseo
    |   |-- etl/                    Mongo raw --> Postgres curated
    |   |-- features/               Feature engineering
    |   |-- models/                 Entrenamiento y evaluación
    |   |-- api/                    FastAPI
    |-- notebooks/                  EDA
    |-- tests/                      Pytest

## Primer arranque

Requisitos: Docker Desktop, Python 3.11+.

    cp .env.example .env
    make venv
    make install
    make up
    make scrape-test

Si el `scrape-test` termina con `bloqueado=False` y anuncios > 0, Idealista deja pasar y seguimos por ahí. Si `bloqueado=True`, pivotamos a Fotocasa (siguiente iteración).

## Roadmap

- [ ] Semana 1: scraper Idealista/Fotocasa + Mongo raw + EDA inicial
- [ ] Semana 2: ETL a Postgres, features geo (OSM POIs, distancia metro), baseline y XGBoost con MLflow
- [ ] Semana 3: intervalos con conformal, FastAPI, Docker, deploy en Cloud Run
- [ ] Bonus: Cloud Scheduler para keep-alive del servicio

## Notas legales

Uso educativo y personal. Se respeta `robots.txt`, se identifica el scraper con un User-Agent honesto, se mantienen delays por página, y no se publican datasets con datos personales o de contacto de anunciantes.

## Autor

Nicolás Rodríguez Pinto. TFM 10/10 UCM (2026). Perfil enfocado a ML aplicado, series temporales, MLOps.
