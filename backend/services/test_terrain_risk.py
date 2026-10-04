from sqlalchemy import text

from database.connection import SessionLocal
from services.terrain_risk import calculate_terrain_risk


def test_all_terrain_risk():
    db = SessionLocal()

    try:
        query = text("""
            SELECT
                mountain_id,
                slope_mean,
                slope_max,
                aspect_mean,
                elevation_min,
                elevation_max,
                slope_below_25_pct,
                slope_25_30_pct,
                slope_30_35_pct,
                slope_35_40_pct,
                slope_40_45_pct,
                slope_above_45_pct
            FROM terrain_features
            ORDER BY mountain_id
        """)

        rows = db.execute(query).mappings().all()

        print("\n8W TERRAIN RISK TEST")
        print("=" * 70)

        for row in rows:

            terrain = {
                "slope_mean": row["slope_mean"],
                "slope_max": row["slope_max"],
                "aspect_mean": row["aspect_mean"],
                "elevation_min": row["elevation_min"],
                "elevation_max": row["elevation_max"],
                "slope_below_25_pct": row["slope_below_25_pct"],
                "slope_25_30_pct": row["slope_25_30_pct"],
                "slope_30_35_pct": row["slope_30_35_pct"],
                "slope_35_40_pct": row["slope_35_40_pct"],
                "slope_40_45_pct": row["slope_40_45_pct"],
                "slope_above_45_pct": row["slope_above_45_pct"],
            }

            result = calculate_terrain_risk(terrain)

            print(
                f"\nMountain ID: {row['mountain_id']}"
            )

            print(
                f"  Terrain score: {result['terrain_score']}/75"
            )

            print(
                f"  Terrain level: {result['terrain_level']}"
            )

            for contributor in result["contributors"]:
                print(
                    f"  {contributor['factor']}: "
                    f"{contributor['value']} "
                    f"[{contributor['severity']}]"
                )

        print("\n" + "=" * 70)
        print(f"Records tested: {len(rows)}")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    test_all_terrain_risk()