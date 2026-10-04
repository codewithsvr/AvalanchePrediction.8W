from sqlalchemy import text

from database.connection import SessionLocal
from database.models import Mountain

from terrain.dem import download_geotiff
from terrain.terrain_features import calculate_terrain_features


def process_all_mountains():
    db = SessionLocal()

    try:
        mountains = db.query(Mountain).all()

        print("\n8W TERRAIN FEATURE EXTRACTION")
        print("=" * 60)
        print(f"Mountains found: {len(mountains)}")
        print("=" * 60)

        successful = 0
        failed = 0

        for mountain in mountains:

            print(f"\nProcessing: {mountain.name}")
            print(
                f"  Coordinates: "
                f"{mountain.latitude}, {mountain.longitude}"
            )

            try:
                # ---------------------------------------------
                # 1. Download DEM
                # ---------------------------------------------
                dem_path = download_geotiff(
                    mountain.latitude,
                    mountain.longitude
                )

                # ---------------------------------------------
                # 2. Calculate terrain features
                # ---------------------------------------------
                features = calculate_terrain_features(
                    dem_path,
                    mountain.latitude,
                    mountain.longitude
                )

                print(
                    f"  Slope mean:      "
                    f"{features['slope_mean']}°"
                )

                print(
                    f"  Slope max:       "
                    f"{features['slope_max']}°"
                )

                print(
                    f"  Aspect mean:     "
                    f"{features['aspect_mean']}°"
                )

                print(
                    f"  Elevation min:   "
                    f"{features['elevation_min']} m"
                )

                print(
                    f"  Elevation max:   "
                    f"{features['elevation_max']} m"
                )

                print(
                    f"  Slope <25°:      "
                    f"{features['slope_below_25_pct']}%"
                )

                print(
                    f"  Slope 25-30°:    "
                    f"{features['slope_25_30_pct']}%"
                )

                print(
                    f"  Slope 30-35°:    "
                    f"{features['slope_30_35_pct']}%"
                )

                print(
                    f"  Slope 35-40°:    "
                    f"{features['slope_35_40_pct']}%"
                )

                print(
                    f"  Slope 40-45°:    "
                    f"{features['slope_40_45_pct']}%"
                )

                print(
                    f"  Slope >45°:      "
                    f"{features['slope_above_45_pct']}%"
                )

                # ---------------------------------------------
                # 3. SQL statement
                # ---------------------------------------------
                sql = text("""
                    INSERT INTO terrain_features
                    (
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
                        slope_above_45_pct,
                        terrain_source
                    )
                    VALUES
                    (
                        :mountain_id,
                        :slope_mean,
                        :slope_max,
                        :aspect_mean,
                        :elevation_min,
                        :elevation_max,
                        :slope_below_25_pct,
                        :slope_25_30_pct,
                        :slope_30_35_pct,
                        :slope_35_40_pct,
                        :slope_40_45_pct,
                        :slope_above_45_pct,
                        :terrain_source
                    )
                    ON DUPLICATE KEY UPDATE
                        slope_mean = VALUES(slope_mean),
                        slope_max = VALUES(slope_max),
                        aspect_mean = VALUES(aspect_mean),
                        elevation_min = VALUES(elevation_min),
                        elevation_max = VALUES(elevation_max),
                        slope_below_25_pct = VALUES(slope_below_25_pct),
                        slope_25_30_pct = VALUES(slope_25_30_pct),
                        slope_30_35_pct = VALUES(slope_30_35_pct),
                        slope_35_40_pct = VALUES(slope_35_40_pct),
                        slope_40_45_pct = VALUES(slope_40_45_pct),
                        slope_above_45_pct = VALUES(slope_above_45_pct),
                        terrain_source = VALUES(terrain_source)
                """)

                # ---------------------------------------------
                # 4. Save to MySQL
                # ---------------------------------------------
                db.execute(
                    sql,
                    {
                        "mountain_id": mountain.id,

                        "slope_mean":
                            features["slope_mean"],

                        "slope_max":
                            features["slope_max"],

                        "aspect_mean":
                            features["aspect_mean"],

                        "elevation_min":
                            features["elevation_min"],

                        "elevation_max":
                            features["elevation_max"],

                        "slope_below_25_pct":
                            features["slope_below_25_pct"],

                        "slope_25_30_pct":
                            features["slope_25_30_pct"],

                        "slope_30_35_pct":
                            features["slope_30_35_pct"],

                        "slope_35_40_pct":
                            features["slope_35_40_pct"],

                        "slope_40_45_pct":
                            features["slope_40_45_pct"],

                        "slope_above_45_pct":
                            features["slope_above_45_pct"],

                        "terrain_source":
                            str(dem_path)
                    }
                )

                # ---------------------------------------------
                # 5. Commit
                # ---------------------------------------------
                db.commit()

                successful += 1

                print(
                    "  ✓ Terrain features saved"
                )

            except Exception as error:

                db.rollback()

                failed += 1

                print(
                    f"  ✗ Failed: {repr(error)}"
                )

        # ---------------------------------------------
        # Final summary
        # ---------------------------------------------
        print("\n" + "=" * 60)
        print("TERRAIN PROCESSING COMPLETE")
        print("=" * 60)
        print(f"Successful: {successful}")
        print(f"Failed:     {failed}")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    process_all_mountains()