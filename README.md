# Housing Madrid: Predictor de precios de vivienda con intervalos de confianza

Un sistema end to end para valorar viviendas en la Comunidad de Madrid con **intervalos de confianza al 90%**, pensado como herramienta interna de una proptech ficticia (Habitrend) para acelerar el trabajo de sus asesores.

En vez de dar un número puntual ("vale 300.000 €"), el modelo devuelve un rango honesto ("entre 280 y 320k con 90% de confianza"). Los asesores usan la anchura del intervalo para decidir cuándo confiar en la valoración automática y cuándo escalar a tasación humana.

Proyecto de portfolio educativo. En construcción activa.

---

## Problema de negocio

Los asesores inmobiliarios valoran viviendas de forma manual con hojas de cálculo y comparativas ad-hoc. Este proceso tarda entre 1 y 2 horas por vivienda y depende mucho de la experiencia del asesor. En un mercado competitivo, el cliente se va a otro sitio si no recibe una cotización rápida.

Este proyecto plantea automatizar la primera valoración manteniendo transparencia sobre la incertidumbre del modelo, para que el asesor mantenga el control y sepa cuándo la máquina se está mojando y cuándo no.

## Métricas de éxito

- **MAPE (error porcentual absoluto medio)** por debajo del 12% en test.
- **Cobertura empírica del intervalo** entre 88% y 92% cuando se promete 90%.
- **Latencia** de la API por debajo de 500 ms por cotización.

## Arquitectura

Scraper (Playwright) → MongoDB (raw)
↓
ETL de limpieza y tipado
↓
PostgreSQL (curated) + POIs de OSM
↓
XGBoost + conformal prediction (MLflow tracking)
↓
FastAPI + Docker + Cloud Run

Doble almacén (raw en Mongo, curated en Postgres) porque la fuente devuelve datos semi estructurados y variables por anuncio. Mongo absorbe la variabilidad sin dolor, Postgres almacena la versión limpia y tipada sobre la que se modela.

## ¿Por qué intervalos y no un valor puntual?

Un valor puntual esconde la incertidumbre. El asesor no sabe si "300k" viene de una zona con miles de datos comparables o de un caso raro donde el modelo prácticamente adivina. Un intervalo estrecho es una señal para el asesor de "puedes cotizar con confianza". Uno ancho es "escala a tasación humana o pide más datos".

Se ha elegido **conformal prediction** porque garantiza cobertura sin asumir normalidad de errores, cosa que en precios de vivienda no se cumple: la varianza escala con el precio y hay colas gordas por outliers.

## Fuentes de datos

- **Fotocasa** como fuente principal, mediante scraper propio con Playwright y rotación de sesión para sortear rate limiting.
- **OpenStreetMap (OSM)** para densidad de puntos de interés (colegios, supermercados, transporte) y distancia a la boca de metro más cercana.

## Estructura del repositorio

housing-madrid/
├── docker-compose.yml         Mongo + Postgres + MLflow
├── .env.example               Plantilla de variables de entorno
├── requirements.txt           Dependencias Python
├── Makefile                   Comandos comunes
├── scripts/init_postgres.sql  Esquema curated
├── src/housing/
│   ├── config.py              Settings centralizados
│   ├── db.py                  Helpers de conexión a Mongo/Postgres
│   ├── scraper/               Playwright y crawlers
│   ├── etl/                   Mongo raw → Postgres curated
│   ├── features/              Feature engineering
│   ├── models/                Entrenamiento y evaluación
│   └── api/                   FastAPI para servir el modelo
├── notebooks/                 Análisis y EDA
└── tests/                     Pytest

## Cómo arrancar en local

Requisitos: Docker Desktop, Python 3.11+.

```bash
cp .env.example .env
python -m venv .venv
.venv\Scripts\Activate.ps1        # PowerShell (Windows)
python -m pip install -r requirements.txt
playwright install chromium
docker compose up -d
```

Prueba de humo del scraper:

```bash
python -m housing.scraper.detail_fotocasa 5
```

## Roadmap

- [x] Set up del stack local (Docker, Mongo, Postgres, MLflow).
- [x] Scraper de descubrimiento y detalle sobre Fotocasa con anti-bot básico.
- [x] Extractor de 60 campos estructurados a partir del JSON embebido.
- [ ] ETL Mongo raw → Postgres curated.
- [ ] EDA y feature engineering en Jupyter.
- [ ] Baseline lineal y XGBoost con tracking en MLflow.
- [ ] Intervalos con conformal prediction, evaluación de cobertura y anchura.
- [ ] API FastAPI con endpoint POST /predict.
- [ ] Deploy en Cloud Run con Artifact Registry.
- [ ] Monitorización básica y retraining schedule.

## Stack técnico

**Lenguajes y librerías**: Python (pandas, NumPy, scikit-learn, XGBoost, LightGBM, mapie, FastAPI, Playwright, pymongo, psycopg).

**Infraestructura**: Docker, MongoDB, PostgreSQL, MLflow.

**Cloud**: GCP (Cloud Run, Artifact Registry, Cloud Storage).

**Otras**: Git, GitHub Actions, pytest, ruff.

## Notas legales

Uso educativo y personal. El scraper respeta `robots.txt`, se identifica con un User-Agent honesto, mantiene delays entre requests y no publica datasets con datos personales o de contacto de anunciantes.

## Autor

Nicolás Rodríguez Pinto. Máster en Ciencia de Datos e Inteligencia de Negocios por la UCM. Perfil enfocado a ML aplicado, series temporales y MLOps.

- Email: nicoro02@ucm.es
- GitHub: [github.com/nicoro02](https://github.com/nicoro02)