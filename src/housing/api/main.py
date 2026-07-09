"""API FastAPI. Por ahora solo el endpoint de health y un placeholder de predict."""
from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="Housing Madrid Price Predictor", version="0.1.0")


class ListingFeatures(BaseModel):
    surface_m2: float
    rooms: int
    bathrooms: int
    property_type: str
    municipality: str
    latitude: float
    longitude: float


class PricePrediction(BaseModel):
    point_eur: float
    lower_eur: float
    upper_eur: float
    coverage_level: float = 0.9


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=PricePrediction)
def predict(features: ListingFeatures) -> PricePrediction:
    # TODO: cargar modelo entrenado y devolver predicción real con intervalo.
    raise NotImplementedError("Endpoint pendiente: se implementa en la semana 3.")
