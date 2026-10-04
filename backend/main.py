from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session

from services.weather import get_weather
from services.risk import calculate_risk

from database.connection import engine, Base, SessionLocal

from database.models import (
    Mountain,
    WeatherObservation,
    RiskPrediction
)
from services.features import get_features

from services.risk_engine import calculate_risk


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="8W Mountain Risk Intelligence API",
    version="0.3.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://avalanche-prediction-8w.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# CORS
# =========================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)


# =========================================================
# ROOT
# =========================================================

@app.get("/")
async def root():

    return {

        "project": "8W",

        "name": "Mountain Risk Intelligence API",

        "status": "online",

        "version": "0.1.0"

    }


# =========================================================
# GET ALL PEAKS
# =========================================================

@app.get("/api/peaks")
async def get_peaks():

    db: Session = SessionLocal()

    try:

        mountains = db.query(Mountain).all()

        return {
            "count": len(mountains),
            "peaks": [
                {
                    "id": mountain.id,
                    "name": mountain.name,
                    "elevation": mountain.elevation,
                    "range": mountain.range,
                    "region": mountain.region,
                    "country": mountain.country,
                    "lat": mountain.latitude,
                    "lon": mountain.longitude,
                    "route": mountain.route
                }

                for mountain in mountains
            ]
        }

    finally:

        db.close()

# =========================================================
# GET SINGLE PEAK
# =========================================================

@app.get("/api/peaks/{peak_id}")
async def get_peak(peak_id: int):

    db: Session = SessionLocal()

    try:

        mountain = (
            db.query(Mountain)
            .filter(Mountain.id == peak_id)
            .first()
        )

        if mountain is None:

            raise HTTPException(
                status_code=404,
                detail="Peak not found"
            )

        return {
            "id": mountain.id,
            "name": mountain.name,
            "elevation": mountain.elevation,
            "range": mountain.range,
            "region": mountain.region,
            "country": mountain.country,
            "lat": mountain.latitude,
            "lon": mountain.longitude,
            "route": mountain.route
        }

    finally:

        db.close()

# =========================================================
# GET WEATHER
# =========================================================
@app.get("/api/peaks/{peak_id}/weather")
async def peak_weather(peak_id: int):

    db = SessionLocal()

    try:

        # ---------------------------------------
        # Find mountain in MySQL
        # ---------------------------------------

        mountain = (
            db.query(Mountain)
            .filter(Mountain.id == peak_id)
            .first()
        )

        if mountain is None:

            raise HTTPException(
                status_code=404,
                detail="Peak not found"
            )


        # ---------------------------------------
        # Get current weather
        # ---------------------------------------

        weather = await get_weather(
            mountain.latitude,
            mountain.longitude
        )


        # ---------------------------------------
        # Extract current conditions
        # ---------------------------------------

        current = weather.get(
            "current",
            {}
        )


        # ---------------------------------------
        # Save observation to MySQL
        # ---------------------------------------

        observation = WeatherObservation(

            mountain_id=mountain.id,

            temperature=current.get(
                "temperature_2m"
            ),

            snowfall=current.get(
                "snowfall"
            ),

            wind_speed=current.get(
                "wind_speed_10m"
            ),

            wind_gust=current.get(
                "wind_gusts_10m"
            ),

            wind_direction=current.get(
                "wind_direction_10m"
            ),

            visibility=current.get(
                "visibility"
            ),

            precipitation=current.get(
                "precipitation"
            )

        )


        db.add(observation)

        db.commit()

        db.refresh(observation)


        # ---------------------------------------
        # Return response
        # ---------------------------------------

        return {

            "peak": mountain.name,

            "location": {

                "latitude": mountain.latitude,

                "longitude": mountain.longitude

            },

            "weather": weather,

            "database": {

                "saved": True,

                "observation_id":
                    observation.id

            }

        }


    except Exception as error:

        db.rollback()

        raise HTTPException(

            status_code=500,

            detail=str(error)

        )


    finally:

        db.close()

# =========================================================
# GET RISK
# =========================================================



@app.get("/api/peaks/{peak_id}/features")
async def peak_features(peak_id: int):

    features = get_features(
        peak_id
    )

    if features is None:

        raise HTTPException(
            status_code=404,
            detail="No weather observations found"
        )

    return features

@app.get("/api/peaks/{peak_id}/risk")
async def peak_risk(peak_id: int):

    features = get_features(
        peak_id
    )

    if features is None:

        raise HTTPException(
            status_code=404,
            detail="No weather observations found"
        )

    risk = calculate_risk(
        features
    )

    return {

        "mountain_id": peak_id,

        "risk": risk

    }
