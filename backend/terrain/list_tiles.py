from database.connection import SessionLocal
from database.models import Mountain
from terrain.dem import get_srtm_tile


db = SessionLocal()

try:

    mountains = db.query(Mountain).all()

    tiles = {}

    for mountain in mountains:

        tile = get_srtm_tile(
            mountain.latitude,
            mountain.longitude
        )

        if tile not in tiles:
            tiles[tile] = []

        tiles[tile].append(
            mountain.name
        )

    print("\n8W REQUIRED SRTM TILES")
    print("-" * 50)

    for tile, mountains_list in sorted(tiles.items()):

        print(
            f"{tile}: "
            + ", ".join(mountains_list)
        )

    print("-" * 50)
    print(
        f"Unique tiles required: {len(tiles)}"
    )

finally:

    db.close()