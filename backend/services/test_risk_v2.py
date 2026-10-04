from database.connection import SessionLocal
from database.models import Mountain

from services.features import get_features
from services.risk_engine import calculate_risk


def test_all_mountains():

    db = SessionLocal()

    try:
        mountains = (
            db.query(Mountain)
            .order_by(Mountain.id)
            .all()
        )

        print("\n8W RISK ENGINE V2 VALIDATION")
        print("=" * 110)

        print(
            f"{'ID':<4}"
            f"{'MOUNTAIN':<20}"
            f"{'WEATHER':>10}"
            f"{'TERRAIN':>10}"
            f"{'FINAL':>10}"
            f"{'LEVEL':<14}"
            f"{'CONF.':>8}"
            f"{'DATA':>8}"
        )

        print("-" * 110)

        results = []

        for mountain in mountains:

            features = get_features(
                mountain.id
            )

            if features is None:
                print(
                    f"{mountain.id:<4}"
                    f"{mountain.name:<20}"
                    f"{'NO DATA':>10}"
                )
                continue

            risk = calculate_risk(
                features
            )

            row = {
                "id": mountain.id,
                "name": mountain.name,
                "weather": risk["weather_score"],
                "terrain": risk["terrain_score"],
                "final": risk["risk_index"],
                "level": risk["risk_level"],
                "confidence": risk["confidence"],
                "data_quality": risk["data_quality"],
            }

            results.append(row)

            print(
                f"{row['id']:<4}"
                f"{row['name']:<20}"
                f"{row['weather']:>10.2f}"
                f"{row['terrain']:>10.2f}"
                f"{row['final']:>10.2f}"
                f"{row['level']:<14}"
                f"{row['confidence']:>8}%"
                f"{row['data_quality']:>8}%"
            )

        # -----------------------------------------------------
        # Summary
        # -----------------------------------------------------

        print("\n" + "=" * 110)
        print("VALIDATION SUMMARY")
        print("=" * 110)

        print(
            f"Mountains tested: {len(results)}"
        )

        if results:

            average_score = (
                sum(
                    r["final"]
                    for r in results
                )
                / len(results)
            )

            highest = max(
                results,
                key=lambda r: r["final"]
            )

            lowest = min(
                results,
                key=lambda r: r["final"]
            )

            print(
                f"Average risk score: "
                f"{average_score:.2f}"
            )

            print(
                f"Highest: "
                f"{highest['name']} "
                f"({highest['final']:.2f})"
            )

            print(
                f"Lowest: "
                f"{lowest['name']} "
                f"({lowest['final']:.2f})"
            )

            # Risk-level distribution
            levels = {}

            for row in results:
                level = row["level"]

                levels[level] = (
                    levels.get(level, 0) + 1
                )

            print("\nRisk level distribution:")

            for level, count in levels.items():
                print(
                    f"  {level:<12}: {count}"
                )

        print("=" * 110)

    finally:
        db.close()


if __name__ == "__main__":
    test_all_mountains()