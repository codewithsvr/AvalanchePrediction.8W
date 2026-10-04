from pathlib import Path
from zipfile import ZipFile
import csv
import io


BASE_DIR = Path(__file__).resolve().parent

ZIP_PATH = (
    BASE_DIR
    / "data"
    / "hiaval"
    / "HiAVAL-v1.2.0.zip"
)


def inspect_csv():

    if not ZIP_PATH.exists():
        print("ERROR: HiAVAL ZIP not found:")
        print(ZIP_PATH)
        return

    print()
    print("=" * 70)
    print("8W HIAVAL DATABASE INSPECTION")
    print("=" * 70)

    with ZipFile(ZIP_PATH, "r") as zip_file:

        # Find HiAVALDB.csv regardless of
        # the internal folder name.
        target_files = [
            filename
            for filename in zip_file.namelist()
            if filename.lower().endswith(
                "/hiavaldb.csv"
            )
        ]

        if not target_files:
            print("ERROR: HiAVALDB.csv not found.")
            return

        target_file = target_files[0]

        print()
        print("Using:")
        print(target_file)

        # ----------------------------------------------------
        # Read CSV directly from ZIP
        # ----------------------------------------------------

        raw_data = zip_file.read(target_file)

        text_data = raw_data.decode(
            "utf-8-sig",
            errors="replace"
        )

        reader = csv.reader(
            io.StringIO(text_data)
        )

        rows = []

        for row in reader:

            rows.append(row)

            if len(rows) >= 6:
                break

        if not rows:
            print("CSV is empty.")
            return

        headers = rows[0]

        print()
        print(
            f"Columns: {len(headers)}"
        )

        print()
        print("-" * 70)
        print("COLUMN NAMES")
        print("-" * 70)

        for index, column in enumerate(headers):

            print(
                f"{index:3}: {column}"
            )

        print()
        print("-" * 70)
        print("FIRST 5 DATA ROWS")
        print("-" * 70)

        for row in rows[1:]:

            print()

            for index, value in enumerate(row):

                column = (
                    headers[index]
                    if index < len(headers)
                    else "UNKNOWN"
                )

                print(
                    f"{column}: {value}"
                )

        print()
        print("=" * 70)


if __name__ == "__main__":
    inspect_csv()