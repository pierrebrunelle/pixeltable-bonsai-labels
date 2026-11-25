"""Generate the fictional bonsai nursery inventory: 16 specimens + one small photo each (offline)."""

from __future__ import annotations

import csv
import random
from pathlib import Path

from PIL import Image, ImageDraw

APP = Path(__file__).parent
DATA = APP / 'data'
PHOTOS = DATA / 'photos'

SPECIES = ['Juniper', 'Ficus', 'Japanese maple', 'Chinese elm', 'Pine', 'Azalea', 'Boxwood', 'Olive']
STYLES = ['formal upright', 'informal upright', 'slanting', 'cascade', 'broom', 'literati']


def photo(path: Path, rng: random.Random, canopy: tuple[int, int, int, int]) -> None:
    img = Image.new('RGB', (160, 120), (236, 232, 222))
    d = ImageDraw.Draw(img)
    d.rectangle((55, 92, 105, 112), fill=(120, 70, 40))  # pot
    d.line((80, 92, 80 + rng.randint(-12, 12), 60), fill=(90, 60, 30), width=5)  # trunk
    d.ellipse(canopy, fill=(40 + rng.randint(0, 40), 110 + rng.randint(0, 60), 50))  # canopy
    img.save(path)


def main() -> None:
    rng = random.Random(20261125)
    PHOTOS.mkdir(parents=True, exist_ok=True)
    rows = []
    for i in range(1, 17):
        x0, y0 = rng.randint(20, 50), rng.randint(10, 30)
        canopy = (x0, y0, x0 + rng.randint(60, 90), y0 + rng.randint(35, 50))
        p = PHOTOS / f'tree-{i:03d}.png'
        photo(p, rng, canopy)
        rows.append(
            {
                'tag_id': 1000 + i,
                'species': rng.choice(SPECIES),
                'style': rng.choice(STYLES),
                'age_years': rng.randint(4, 60),
                'height_cm': round(rng.uniform(12, 75), 1),
                'pot_size_in': rng.choice([6, 8, 10, 12, 14]),
                'photo': f'data/photos/{p.name}',
            }
        )
    with open(DATA / 'specimens.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f'wrote {len(rows)} specimens + photos under {DATA.name}/')


if __name__ == '__main__':
    main()
