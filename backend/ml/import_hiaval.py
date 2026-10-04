from pathlib import Path
from zipfile import ZipFile
import csv
import io
from datetime import date

from sqlalchemy import text

from database.connection import SessionLocal


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ZIP_PATH = (
    BASE_DIR
    / "data"
    / "hiaval"
    / "HiAVAL-v1.2.0.zip"
)


# ============================================================
# FIND HIAVAL CSV
# ============================================================

def find_hiaval_csv(zip_file):

    matches = [
        filename
        for filename in zip_file.namelist()
        if filename.lower().endswith(
            "/hiavaldb.csv"
        )
    ]

    if not matches:
        raise FileNotFoundError(
            "HiAVALDB.csv not found inside ZIP"
        )

    return matches[0]


# ============================================================
# CLEAN VALUE
# ============================================================

def clean_value(value):

    if value is None:
        return None

    value = value.strip()

    if value == "":
        return None

    if value.upper() == "NA":
        return None

    return value


# ============================================================
# PARSE INTEGER
# ============================================================

def parse_int(value):

    value = clean_value(value)

    if value is None:
        return None

    try:
        return int(float(value))

    except (ValueError, TypeError):
        return None


# ============================================================
# PARSE FLOAT
# ============================================================

def parse_float(value):

    value = clean_value(value)

    if value is None:
        return None

    try:
        return float(value)

    except (ValueError, TypeError):
        return None


# ============================================================
# PARSE DATE
# ============================================================

def parse_date(year, month, day):

    year = parse_int(year)
    month = parse_int(month)
    day = parse_int(day)

    if (
        year is None
        or month is None
        or day is None
    ):
        return None

    try:

        return date(
            year,
            month,
            day
        )

    except ValueError:

        return None


# ============================================================
# MAIN IMPORT FUNCTION
# ============================================================

def import_hiaval():

    if not ZIP_PATH.exists():

        raise FileNotFoundError(
            f"HiAVAL ZIP not found:\n{ZIP_PATH}"
        )

    db = SessionLocal()

    try:

        print()
        print("=" * 70)
        print("8W HIAVAL IMPORT")
        print("=" * 70)

        # ====================================================
        # OPEN ZIP
        # ====================================================

        with ZipFile(
            ZIP_PATH,
            "r"
        ) as zip_file:

            csv_path = find_hiaval_csv(
                zip_file
            )

            print(
                f"Source: {csv_path}"
            )

            # =================================================
            # READ CSV
            # =================================================

            raw_data = zip_file.read(
                csv_path
            )

            text_data = raw_data.decode(
                "utf-8-sig",
                errors="replace"
            )

            reader = csv.DictReader(
                io.StringIO(text_data)
            )

            # =================================================
            # VERIFY COLUMNS
            # =================================================

            required_columns = {
                "Location",
                "Year",
                "Month",
                "Day",
                "Latitude",
                "Longitude",
                "Country",
                "Region_HiMAP",
                "Type",
                "Impact",
                "Fatalities",
                "Injured",
                "Livestock",
                "Leisure",
                "Remarks",
                "Reference"
            }

            actual_columns = set(
                reader.fieldnames or []
            )

            missing_columns = (
                required_columns
                - actual_columns
            )

            if missing_columns:

                raise ValueError(
                    "Missing HiAVAL columns: "
                    f"{missing_columns}"
                )

            # =================================================
            # SQL
            # =================================================

            sql = text("""
                INSERT INTO avalanche_events
                (
                    location,

                    event_year,
                    event_month,
                    event_day,
                    event_date,

                    latitude,
                    longitude,

                    country,
                    region_himap,

                    avalanche_type,
                    impact,

                    fatalities,
                    injured,
                    livestock,

                    leisure,

                    remarks,
                    reference_url,

                    source
                )
                VALUES
                (
                    :location,

                    :event_year,
                    :event_month,
                    :event_day,
                    :event_date,

                    :latitude,
                    :longitude,

                    :country,
                    :region_himap,

                    :avalanche_type,
                    :impact,

                    :fatalities,
                    :injured,
                    :livestock,

                    :leisure,

                    :remarks,
                    :reference_url,

                    'HiAVAL v1.2.0'
                )

                ON DUPLICATE KEY UPDATE

                    event_date =
                        VALUES(event_date),

                    avalanche_type =
                        VALUES(avalanche_type),

                    impact =
                        VALUES(impact),

                    fatalities =
                        VALUES(fatalities),

                    injured =
                        VALUES(injured),

                    remarks =
                        VALUES(remarks),

                    reference_url =
                        VALUES(reference_url)
            """)

            # =================================================
            # COUNTERS
            # =================================================

            processed = 0
            complete_dates = 0
            incomplete_dates = 0
            skipped_records = 0
            failed = 0

            failed_rows = []

            skipped_rows = []

            # =================================================
            # PROCESS RECORDS
            # =================================================

            for row_number, row in enumerate(
                reader,
                start=2
            ):

                try:

                    # -----------------------------------------
                    # YEAR
                    # -----------------------------------------

                    raw_year = clean_value(
                        row["Year"]
                    )

                    event_year = parse_int(
                        raw_year
                    )

                    # -----------------------------------------
                    # MULTI-YEAR / INVALID YEAR
                    #
                    # Example:
                    # "2002 - 2008"
                    #
                    # Cannot be represented by event_year INT
                    # and cannot be used as a dated ML event.
                    # -----------------------------------------

                    if event_year is None:

                        incomplete_dates += 1
                        skipped_records += 1

                        skipped_rows.append({
                            "row_number":
                                row_number,

                            "reason":
                                "Non-specific year",

                            "year":
                                raw_year,

                            "location":
                                clean_value(
                                    row["Location"]
                                )
                        })

                        continue

                    # -----------------------------------------
                    # MONTH / DAY
                    # -----------------------------------------

                    event_month = parse_int(
                        row["Month"]
                    )

                    event_day = parse_int(
                        row["Day"]
                    )

                    # -----------------------------------------
                    # COMPLETE DATE
                    # -----------------------------------------

                    event_date = parse_date(
                        row["Year"],
                        row["Month"],
                        row["Day"]
                    )

                    if event_date is not None:

                        complete_dates += 1

                    else:

                        incomplete_dates += 1

                    # -----------------------------------------
                    # PREPARE VALUES
                    # -----------------------------------------

                    values = {

                        "location":
                            clean_value(
                                row["Location"]
                            ),

                        "event_year":
                            event_year,

                        "event_month":
                            event_month,

                        "event_day":
                            event_day,

                        "event_date":
                            event_date,

                        "latitude":
                            parse_float(
                                row["Latitude"]
                            ),

                        "longitude":
                            parse_float(
                                row["Longitude"]
                            ),

                        "country":
                            clean_value(
                                row["Country"]
                            ),

                        "region_himap":
                            parse_int(
                                row["Region_HiMAP"]
                            ),

                        "avalanche_type":
                            clean_value(
                                row["Type"]
                            ),

                        "impact":
                            clean_value(
                                row["Impact"]
                            ),

                        "fatalities":
                            parse_int(
                                row["Fatalities"]
                            ),

                        "injured":
                            parse_int(
                                row["Injured"]
                            ),

                        "livestock":
                            clean_value(
                                row["Livestock"]
                            ),

                        "leisure":
                            clean_value(
                                row["Leisure"]
                            ),

                        "remarks":
                            clean_value(
                                row["Remarks"]
                            ),

                        "reference_url":
                            clean_value(
                                row["Reference"]
                            )
                    }

                    # -----------------------------------------
                    # INSERT
                    #
                    # Nested transaction means one bad row
                    # cannot damage the remaining import.
                    # -----------------------------------------

                    with db.begin_nested():

                        db.execute(
                            sql,
                            values
                        )

                    processed += 1

                except Exception as error:

                    failed += 1

                    failed_rows.append({
                        "row_number":
                            row_number,

                        "error":
                            repr(error),

                        "row":
                            dict(row)
                    })

            # =================================================
            # COMMIT
            # =================================================

            db.commit()

        # ====================================================
        # FINAL REPORT
        # ====================================================

        print()
        print("=" * 70)
        print("HIAVAL IMPORT COMPLETE")
        print("=" * 70)

        print(
            f"Records processed: "
            f"{processed}"
        )

        print(
            f"Complete dates: "
            f"{complete_dates}"
        )

        print(
            f"Incomplete dates: "
            f"{incomplete_dates}"
        )

        print(
            f"Skipped records: "
            f"{skipped_records}"
        )

        print(
            f"Failed rows: "
            f"{failed}"
        )

        # ====================================================
        # SKIPPED RECORD DETAILS
        # ====================================================

        if skipped_rows:

            print()
            print("-" * 70)
            print("SKIPPED NON-SPECIFIC RECORDS")
            print("-" * 70)

            for item in skipped_rows:

                print(
                    f"CSV Row: "
                    f"{item['row_number']} | "
                    f"Year: "
                    f"{item['year']} | "
                    f"Location: "
                    f"{item['location']}"
                )

            print("-" * 70)

        # ====================================================
        # FAILED ROW DETAILS
        # ====================================================

        if failed_rows:

            print()
            print("=" * 70)
            print("FAILED ROW DETAILS")
            print("=" * 70)

            for item in failed_rows:

                print()

                print(
                    f"CSV Row: "
                    f"{item['row_number']}"
                )

                print(
                    f"Error: "
                    f"{item['error']}"
                )

                print()

                print(
                    "Data:"
                )

                print(
                    item["row"]
                )

            print()
            print("=" * 70)

        print()

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    import_hiaval()