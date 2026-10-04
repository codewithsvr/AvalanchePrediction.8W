from math import radians, sin, cos, sqrt, atan2

from sqlalchemy import text

from database.connection import SessionLocal


# ============================================================
# CONFIGURATION
# ============================================================

MATCH_RADIUS_KM = 50.0


# ============================================================
# HAVERSINE DISTANCE
# ============================================================

def haversine_distance(
    latitude_1,
    longitude_1,
    latitude_2,
    longitude_2
):
    """
    Calculate great-circle distance between
    two latitude/longitude coordinates.

    Returns distance in kilometres.
    """

    earth_radius_km = 6371.0

    lat1 = radians(latitude_1)
    lon1 = radians(longitude_1)

    lat2 = radians(latitude_2)
    lon2 = radians(longitude_2)

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (
        sin(delta_lat / 2) ** 2
        +
        cos(lat1)
        * cos(lat2)
        * sin(delta_lon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return earth_radius_km * c


# ============================================================
# LOAD MOUNTAINS
# ============================================================

def load_mountains(db):

    rows = db.execute(
        text("""
            SELECT
                id,
                name,
                latitude,
                longitude
            FROM mountains
            ORDER BY id
        """)
    ).fetchall()

    return rows


# ============================================================
# LOAD HIAVAL EVENTS
# ============================================================

def load_events(db):

    rows = db.execute(
        text("""
            SELECT
                id,
                location,
                event_date,
                latitude,
                longitude
            FROM avalanche_events
            WHERE event_date IS NOT NULL
              AND latitude IS NOT NULL
              AND longitude IS NOT NULL
            ORDER BY event_date
        """)
    ).fetchall()

    return rows


# ============================================================
# SAVE MATCH
# ============================================================

def save_match(
    db,
    event_id,
    mountain_id,
    distance_km,
    event_date
):

    db.execute(
        text("""
            INSERT INTO avalanche_event_matches
            (
                avalanche_event_id,
                mountain_id,
                distance_km,
                event_date
            )
            VALUES
            (
                :event_id,
                :mountain_id,
                :distance_km,
                :event_date
            )
            ON DUPLICATE KEY UPDATE

                distance_km =
                    VALUES(distance_km),

                event_date =
                    VALUES(event_date)
        """),
        {
            "event_id":
                event_id,

            "mountain_id":
                mountain_id,

            "distance_km":
                distance_km,

            "event_date":
                event_date
        }
    )


# ============================================================
# MAIN
# ============================================================

def match_events():

    db = SessionLocal()

    try:

        print()
        print("=" * 70)
        print("8W HIAVAL → MOUNTAIN MATCHING")
        print("=" * 70)

        # ----------------------------------------------------
        # Load mountains
        # ----------------------------------------------------

        mountains = load_mountains(db)

        print(
            f"Mountains loaded: "
            f"{len(mountains)}"
        )

        # ----------------------------------------------------
        # Load events
        # ----------------------------------------------------

        events = load_events(db)

        print(
            f"Dated events with coordinates: "
            f"{len(events)}"
        )

        print(
            f"Matching radius: "
            f"{MATCH_RADIUS_KM} km"
        )

        print("=" * 70)

        matched = 0
        unmatched = 0

        # ----------------------------------------------------
        # Process every event
        # ----------------------------------------------------

        for event in events:

            nearest_mountain = None
            nearest_distance = None

            # ------------------------------------------------
            # Compare against all 14 mountains
            # ------------------------------------------------

            for mountain in mountains:

                distance = haversine_distance(
                    event.latitude,
                    event.longitude,
                    mountain.latitude,
                    mountain.longitude
                )

                if (
                    nearest_distance is None
                    or distance < nearest_distance
                ):

                    nearest_distance = distance
                    nearest_mountain = mountain

            # ------------------------------------------------
            # Keep only events within radius
            # ------------------------------------------------

            if (
                nearest_mountain is not None
                and nearest_distance
                <= MATCH_RADIUS_KM
            ):

                save_match(
                    db,
                    event.id,
                    nearest_mountain.id,
                    nearest_distance,
                    event.event_date
                )

                matched += 1

            else:

                unmatched += 1

        # ----------------------------------------------------
        # Commit
        # ----------------------------------------------------

        db.commit()

        print()
        print("=" * 70)
        print("MATCHING COMPLETE")
        print("=" * 70)

        print(
            f"Matched events: "
            f"{matched}"
        )

        print(
            f"Unmatched events: "
            f"{unmatched}"
        )

        print(
            f"Total processed: "
            f"{matched + unmatched}"
        )

        print("=" * 70)

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    match_events()