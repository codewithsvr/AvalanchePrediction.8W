from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    Numeric,
    ForeignKey,
    UniqueConstraint,
    Text,
    func
)

from .connection import Base


# ============================================================
# MOUNTAINS
# ============================================================

class Mountain(Base):

    __tablename__ = "mountains"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    elevation = Column(
        Integer,
        nullable=False
    )

    range = Column(
        String(100)
    )

    region = Column(
        String(150)
    )

    country = Column(
        String(100)
    )

    latitude = Column(
        Float,
        nullable=False
    )

    longitude = Column(
        Float,
        nullable=False
    )

    route = Column(
        String(150)
    )


# ============================================================
# WEATHER OBSERVATIONS
# ============================================================

class WeatherObservation(Base):

    __tablename__ = "weather_observations"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    mountain_id = Column(
        Integer,
        ForeignKey("mountains.id"),
        nullable=False
    )

    timestamp = Column(
        DateTime,
        default=datetime.utcnow
    )

    temperature = Column(Float)

    snowfall = Column(Float)

    snow_depth = Column(Float)

    wind_speed = Column(Float)

    wind_gust = Column(Float)

    wind_direction = Column(Float)

    visibility = Column(Float)

    precipitation = Column(Float)


# ============================================================
# RISK PREDICTIONS
# ============================================================

class RiskPrediction(Base):

    __tablename__ = "risk_predictions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    mountain_id = Column(
        Integer,
        ForeignKey("mountains.id"),
        nullable=False
    )

    timestamp = Column(
        DateTime,
        default=datetime.utcnow
    )

    risk_score = Column(Float)

    risk_category = Column(
        String(50)
    )

    model_version = Column(
        String(50)
    )

    confidence = Column(Float)


# ============================================================
# TERRAIN FEATURES
# ============================================================

class TerrainFeature(Base):

    __tablename__ = "terrain_features"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    mountain_id = Column(
        Integer,
        ForeignKey("mountains.id"),
        nullable=False
    )

    slope_mean = Column(
        Numeric(6, 2)
    )

    slope_max = Column(
        Numeric(6, 2)
    )

    aspect_mean = Column(
        Numeric(6, 2)
    )

    elevation_min = Column(
        Numeric(8, 2)
    )

    elevation_max = Column(
        Numeric(8, 2)
    )

    terrain_source = Column(
        String(255)
    )

    slope_below_25_pct = Column(
        Numeric(6, 2)
    )

    slope_25_30_pct = Column(
        Numeric(6, 2)
    )

    slope_30_35_pct = Column(
        Numeric(6, 2)
    )

    slope_35_40_pct = Column(
        Numeric(6, 2)
    )

    slope_40_45_pct = Column(
        Numeric(6, 2)
    )

    slope_above_45_pct = Column(
        Numeric(6, 2)
    )

    created_at = Column(
        DateTime,
        server_default=func.current_timestamp()
    )

    __table_args__ = (
        UniqueConstraint(
            "mountain_id",
            name="uq_terrain_mountain"
        ),
    )


# ============================================================
# HISTORICAL AVALANCHE FEATURES
# ============================================================

class HistoricalAvalancheFeature(Base):

    __tablename__ = "historical_avalanche_features"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    mountain_id = Column(
        Integer,
        ForeignKey("mountains.id"),
        nullable=False
    )

    basin = Column(
        String(100),
        nullable=False
    )

    radius_m = Column(
        Integer,
        nullable=False
    )

    total_pixels = Column(
        Integer,
        nullable=False
    )

    valid_pixels = Column(
        Integer,
        nullable=False
    )

    coverage_pct = Column(
        Numeric(8, 3)
    )

    mean_frequency = Column(
        Numeric(8, 3)
    )

    max_frequency = Column(
        Integer
    )

    frequency_5plus_pct = Column(
        Numeric(8, 3)
    )

    frequency_10plus_pct = Column(
        Numeric(8, 3)
    )

    frequency_20plus_pct = Column(
        Numeric(8, 3)
    )

    source = Column(
        String(255)
    )

    created_at = Column(
        DateTime,
        server_default=func.current_timestamp()
    )

    __table_args__ = (
        UniqueConstraint(
            "mountain_id",
            "radius_m",
            name="uq_historical_mountain_radius"
        ),
    )


# ============================================================
# HIAVAL AVALANCHE EVENTS
# ============================================================

class AvalancheEvent(Base):

    __tablename__ = "avalanche_events"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    location = Column(
        String(255)
    )

    event_year = Column(
        Integer,
        nullable=False
    )

    event_month = Column(
        Integer
    )

    event_day = Column(
        Integer
    )

    event_date = Column(
        Date
    )

    latitude = Column(
        Numeric(10, 6)
    )

    longitude = Column(
        Numeric(10, 6)
    )

    country = Column(
        String(100)
    )

    region_himap = Column(
        Integer
    )

    avalanche_type = Column(
        String(100)
    )

    impact = Column(
        String(20)
    )

    fatalities = Column(
        Integer
    )

    injured = Column(
        Integer
    )

    livestock = Column(
        String(50)
    )

    leisure = Column(
        String(20)
    )

    remarks = Column(
        Text
    )

    reference_url = Column(
        Text
    )

    source = Column(
        String(100),
        default="HiAVAL v1.2.0"
    )

    created_at = Column(
        DateTime,
        server_default=func.current_timestamp()
    )

    __table_args__ = (
        UniqueConstraint(
            "location",
            "event_year",
            "event_month",
            "event_day",
            "latitude",
            "longitude",
            name="uq_avalanche_event"
        ),
    )


# ============================================================
# AVALANCHE EVENT ↔ MOUNTAIN MATCHES
# ============================================================

class AvalancheEventMatch(Base):

    __tablename__ = "avalanche_event_matches"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    avalanche_event_id = Column(
        Integer,
        ForeignKey("avalanche_events.id"),
        nullable=False
    )

    mountain_id = Column(
        Integer,
        ForeignKey("mountains.id"),
        nullable=False
    )

    distance_km = Column(
        Numeric(10, 3),
        nullable=False
    )

    event_date = Column(
        Date
    )

    created_at = Column(
        DateTime,
        server_default=func.current_timestamp()
    )

    __table_args__ = (
        UniqueConstraint(
            "avalanche_event_id",
            "mountain_id",
            name="uq_event_mountain_match"
        ),
    )


# ============================================================
# WEATHER AROUND AVALANCHE EVENTS
# ============================================================

class AvalancheEventWeather(Base):

    __tablename__ = "avalanche_event_weather"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    avalanche_event_id = Column(
        Integer,
        ForeignKey("avalanche_events.id"),
        nullable=False
    )

    mountain_id = Column(
        Integer,
        ForeignKey("mountains.id"),
        nullable=False
    )

    timestamp = Column(
        DateTime,
        nullable=False
    )

    temperature = Column(
        Numeric(8, 3)
    )

    snowfall = Column(
        Numeric(8, 3)
    )

    snow_depth = Column(
        Numeric(8, 3)
    )

    wind_speed = Column(
        Numeric(8, 3)
    )

    wind_gust = Column(
        Numeric(8, 3)
    )

    source = Column(
        String(100),
        default="Open-Meteo ERA5"
    )

    created_at = Column(
        DateTime,
        server_default=func.current_timestamp()
    )

    __table_args__ = (
        UniqueConstraint(
            "avalanche_event_id",
            "timestamp",
            name="uq_event_weather_timestamp"
        ),
    )


# ============================================================
# AVALANCHE EVENT FEATURES
# ============================================================
# ============================================================
# AVALANCHE EVENT FEATURES
# ============================================================

class AvalancheEventFeature(Base):

    __tablename__ = "avalanche_event_features"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    avalanche_event_id = Column(
        Integer,
        ForeignKey("avalanche_events.id"),
        nullable=False
    )

    mountain_id = Column(
        Integer,
        ForeignKey("mountains.id"),
        nullable=False
    )

    event_date = Column(Date)

    distance_km = Column(
        Numeric(10, 3)
    )

    match_type = Column(
        String(20)
    )

    snowfall_24h = Column(
        Numeric(10, 3)
    )

    snowfall_48h = Column(
        Numeric(10, 3)
    )

    snowfall_72h = Column(
        Numeric(10, 3)
    )

    max_wind_24h = Column(
        Numeric(10, 3)
    )

    max_gust_24h = Column(
        Numeric(10, 3)
    )

    temperature_min = Column(
        Numeric(10, 3)
    )

    temperature_max = Column(
        Numeric(10, 3)
    )

    mean_temperature = Column(
        Numeric(10, 3)
    )

    temperature_change = Column(
        Numeric(10, 3)
    )

    snow_depth_min = Column(
        Numeric(10, 3)
    )

    snow_depth_max = Column(
        Numeric(10, 3)
    )

    snow_depth_change = Column(
        Numeric(10, 3)
    )

    mean_wind_speed = Column(
        Numeric(10, 3)
    )

    slope_mean = Column(
        Numeric(10, 3)
    )

    slope_above_45_pct = Column(
        Numeric(10, 3)
    )

    elevation_range = Column(
        Numeric(10, 3)
    )

    historical_mean_frequency = Column(
        Numeric(10, 3)
    )

    historical_max_frequency = Column(
        Integer
    )

    historical_5plus_pct = Column(
        Numeric(10, 3)
    )

    historical_10plus_pct = Column(
        Numeric(10, 3)
    )

    historical_20plus_pct = Column(
        Numeric(10, 3)
    )

    historical_coverage_pct = Column(
        Numeric(10, 3)
    )

    label = Column(
        Integer,
        default=1
    )

    created_at = Column(
        DateTime,
        server_default=func.current_timestamp()
    )

    __table_args__ = (
        UniqueConstraint(
            "avalanche_event_id",
            name="uq_avalanche_event_feature"
        ),
    )


# ============================================================
# ML CONTROL SAMPLES
# ============================================================

class MlControlSample(Base):

    __tablename__ = "ml_control_samples"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    mountain_id = Column(
        Integer,
        ForeignKey("mountains.id"),
        nullable=False
    )

    control_date = Column(
        Date,
        nullable=False
    )

    source = Column(
        String(100),
        default="Open-Meteo ERA5"
    )

    snowfall_24h = Column(
        Numeric(10, 3)
    )

    snowfall_48h = Column(
        Numeric(10, 3)
    )

    snowfall_72h = Column(
        Numeric(10, 3)
    )

    max_wind_24h = Column(
        Numeric(10, 3)
    )

    max_gust_24h = Column(
        Numeric(10, 3)
    )

    temperature_min = Column(
        Numeric(10, 3)
    )

    temperature_max = Column(
        Numeric(10, 3)
    )

    mean_temperature = Column(
        Numeric(10, 3)
    )

    temperature_change = Column(
        Numeric(10, 3)
    )

    snow_depth_min = Column(
        Numeric(10, 3)
    )

    snow_depth_max = Column(
        Numeric(10, 3)
    )

    snow_depth_change = Column(
        Numeric(10, 3)
    )

    mean_wind_speed = Column(
        Numeric(10, 3)
    )

    slope_mean = Column(
        Numeric(10, 3)
    )

    slope_above_45_pct = Column(
        Numeric(10, 3)
    )

    elevation_range = Column(
        Numeric(10, 3)
    )

    historical_mean_frequency = Column(
        Numeric(10, 3)
    )

    historical_max_frequency = Column(
        Integer
    )

    historical_5plus_pct = Column(
        Numeric(10, 3)
    )

    historical_10plus_pct = Column(
        Numeric(10, 3)
    )

    historical_20plus_pct = Column(
        Numeric(10, 3)
    )

    historical_coverage_pct = Column(
        Numeric(10, 3)
    )

    matched_positive_event_id = Column(
        Integer
    )

    label = Column(
        Integer,
        default=0
    )

    created_at = Column(
        DateTime,
        server_default=func.current_timestamp()
    )

    __table_args__ = (
        UniqueConstraint(
            "mountain_id",
            "control_date",
            name="uq_control_mountain_date"
        ),
    )