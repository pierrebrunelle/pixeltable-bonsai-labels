<!-- pixeltable-example-app: 20261125-bonsai-labels -->
# bonsai nursery labeling round-trip built with Pixeltable

![bonsai nursery labeling round-trip built with Pixeltable](.github/social-preview.png)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/pierrebrunelle/pixeltable-bonsai-labels?quickstart=1)
[![Built with Pixeltable](https://img.shields.io/badge/built%20with-Pixeltable-5b4bff)](https://pixeltable.com)
[![PyPI - pixeltable](https://img.shields.io/pypi/v/pixeltable?label=pixeltable)](https://pypi.org/project/pixeltable/)
[![GitHub stars](https://img.shields.io/github/stars/pixeltable/pixeltable?style=social)](https://github.com/pixeltable/pixeltable)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

A bonsai nursery keeps its trees in a Pixeltable table: tag, species, style, age, height, pot size and a photo, with computed columns for the canopy bounding box (found in the photo) and the pot size in centimetres. Graders label each tree's health outside Pixeltable, so roundtrip.py exports the table (pxt.io.export_csv, export_json, export_parquet, a COCO dataset with one canopy box per tree, and a PyTorch DataLoader over the labelled rows), lets the grader edit the CSV, and imports it back with pxt.io.import_csv and explicit column types. A re-measured pot typed as 9.5 inches is refused instead of being silently truncated to 9, since Pixeltable 0.7.26 rejects lossy float-to-int conversions on import; the batch is either fixed or applied without that row. The staged file is joined to the live table by tag, only changed rows go through batch_update, and every batch is logged with the Specimens versions before and after, so `diff` shows the field changes between any two versions and `undo` reverts the last batch.

[Pixeltable](https://pixeltable.com) is open-source, Python-native **multimodal AI data infrastructure**: tables, incremental computed columns, UDFs, indexes and serving in one library, running locally or on Pixeltable Cloud.

> ⭐ **Like this example?** Star [pixeltable/pixeltable](https://github.com/pixeltable/pixeltable) on GitHub. It helps other developers find it.

## What this example shows

- **Incremental computed columns** powered by plain Python UDFs (`@pxt.udf`)
- **Multimodal media columns** with configurable media destinations
- **Versioning**: table history, snapshots and revert for an auditable trail
- **Importable UDF module**: UDFs live in `udfs.py`; tables and queries live in `app.py` (Pixeltable resolves UDFs by module path)
- **`pixeltable.toml`** declares a local database and a **Pixeltable Cloud** database, so the same code deploys with `pxt db update`



## What's inside

| File | What it is |
|------|------------|
| `.devcontainer/devcontainer.json` | GitHub Codespaces / Dev Container config: Python 3.12, installs `requirements.txt` |
| `.github/social-preview.png` | Social preview image (1280x640) |
| `CITATION.cff` | Citation metadata (authors, license, release date, keywords) |
| `app.py` | Tables declared as Python classes and `@pxt.query` functions |
| `data/edited/batch-1.csv` | Sample data |
| `data/edited/batch-2.csv` | Sample data |
| `data/photos/tree-001.png` | Sample data |
| `data/photos/tree-002.png` | Sample data |
| `data/photos/tree-003.png` | Sample data |
| `data/photos/tree-004.png` | Sample data |
| `data/photos/tree-005.png` | Sample data |
| `data/photos/tree-006.png` | Sample data |
| `data/photos/tree-007.png` | Sample data |
| `data/photos/tree-008.png` | Sample data |
| `data/photos/tree-009.png` | Sample data |
| `data/photos/tree-010.png` | Sample data |
| `data/photos/tree-011.png` | Sample data |
| `data/photos/tree-012.png` | Sample data |
| `data/photos/tree-013.png` | Sample data |
| `data/photos/tree-014.png` | Sample data |
| `data/photos/tree-015.png` | Sample data |
| `data/photos/tree-016.png` | Sample data |
| `data/specimens.csv` | Sample data |
| `make_data.py` | Generate the fictional bonsai nursery inventory: 16 specimens + one small photo each (offline) |
| `pixeltable.toml` | Project config: the local database plus a Pixeltable Cloud database (sizing, deploy excludes) |
| `roundtrip.py` | Export -> edit externally -> re-import -> diff, for the bonsai nursery's health labels |
| `udfs.py` | Pixeltable UDFs (`@pxt.udf`) in their own importable module, imported by `app.py` |
| `requirements.txt` / `pyproject.toml` | Dependencies (`pixeltable>=0.7.26`) |

**Tables**

| Table | Stored columns | Computed columns |
|-------|---------|------------------|
| `specimens` | `tag_id`, `species`, `style`, `age_years`, `height_cm`, `pot_size_in`, `photo`, `health`, `grader` | `canopy`, `thumb` |
| `label_batches` | `batch_id`, `file_name`, `file_format`, `rows_in`, `rows_changed`, `rejected`, `version_before`, `version_after`, `applied_at` | - |

## Run in your browser (GitHub Codespaces)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/pierrebrunelle/pixeltable-bonsai-labels?quickstart=1)

1. Click **Open in GitHub Codespaces** above (or [this link](https://codespaces.new/pierrebrunelle/pixeltable-bonsai-labels?quickstart=1)). The dev container installs Python 3.12 and `pixeltable>=0.7.26` from `requirements.txt`.
2. In the codespace terminal, create the tables, seed them and run the app:

   ```bash
   pxt schema update app.py bonsai
   python make_data.py                     # 16 fictional trees + a small photo each (offline)
   python roundtrip.py seed
   python roundtrip.py export csv          # also: json, parquet, coco, pytorch
   python roundtrip.py grade output/export-csv/specimens.csv data/edited/batch-1.csv --typo
   python roundtrip.py apply data/edited/batch-1.csv               # refused: pot size 9.5 is not a whole number
   python roundtrip.py apply data/edited/batch-1.csv --skip-lossy  # applies the other rows, logs the skipped tag
   python roundtrip.py diff 1 2           # field changes between two table versions
   python roundtrip.py undo               # revert the last batch
   python roundtrip.py report             # label counts, review queue, batch log -> output/labels.md
   BONSAI_NS=pxt://<your-org>:<your-db>/bonsai python roundtrip.py seed   # the same loop on Pixeltable Cloud, after: pxt schema update app.py pxt://<your-org>:<your-db>/bonsai (COCO/PyTorch exports need the local catalog)
   ```


## Quickstart

Requires Python 3.11+ and `pixeltable>=0.7.26`.

```bash
git clone https://github.com/pierrebrunelle/pixeltable-bonsai-labels.git
cd pixeltable-bonsai-labels
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Create the tables in a local catalog directory named `bonsai`
pxt schema update app.py bonsai

python make_data.py                     # 16 fictional trees + a small photo each (offline)
python roundtrip.py seed
python roundtrip.py export csv          # also: json, parquet, coco, pytorch
python roundtrip.py grade output/export-csv/specimens.csv data/edited/batch-1.csv --typo
python roundtrip.py apply data/edited/batch-1.csv               # refused: pot size 9.5 is not a whole number
python roundtrip.py apply data/edited/batch-1.csv --skip-lossy  # applies the other rows, logs the skipped tag
python roundtrip.py diff 1 2           # field changes between two table versions
python roundtrip.py undo               # revert the last batch
python roundtrip.py report             # label counts, review queue, batch log -> output/labels.md
BONSAI_NS=pxt://<your-org>:<your-db>/bonsai python roundtrip.py seed   # the same loop on Pixeltable Cloud, after: pxt schema update app.py pxt://<your-org>:<your-db>/bonsai (COCO/PyTorch exports need the local catalog)
```

## Deploy to Pixeltable Cloud

The same `app.py` runs on [Pixeltable Cloud](https://pixeltable.com). Sign in (or get a free trial database with `pxt new`), point the second database entry in `pixeltable.toml` at your own database, then deploy:

```bash
pxt login                       # or: export PIXELTABLE_API_KEY=<your-api-key>
# edit pixeltable.toml: name = 'pxt://<your-org>:<your-db>'
pxt db update pxt://<your-org>:<your-db>                 # build the image and upload the project
pxt schema update app.py pxt://<your-org>:<your-db>       # create the tables at the database root (no per-app folder)
```

Keep keys in environment variables or `pxt secret set`, never in code.

## Code walkthrough

**1. Business logic is plain Python, in `udfs.py`.** A `@pxt.udf` function can be used as a column expression. Pixeltable records UDFs by module path (`udfs.canopy_bbox`), so they live in their own importable module rather than inline in the app: the daemon, serving workers and Pixeltable Cloud import it again by that path.

```python
# udfs.py
@pxt.udf
def canopy_bbox(photo: PIL.Image.Image) -> list[int]:
    """Bounding box [x, y, w, h] of the green canopy in a specimen photo (COCO bbox order)."""
    rgb = photo.convert('RGB')
    w, h = rgb.size
    px = rgb.load()
    xs, ys = [], []
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if g - r > GREEN_MARGIN and g - b > GREEN_MARGIN:
                xs.append(x)
                ys.append(y)
    if not xs:
        return [0, 0, 0, 0]
    return [min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1]
```

**2. Tables are Python classes (`app.py`).** Annotated attributes are stored columns; attributes assigned an expression are **computed columns** (`canopy`, `thumb`), evaluated incrementally on every insert or update and recomputed when their inputs change.

```python
# app.py
class Specimens(TableModel, name='specimens'):
    """One tree in the nursery; `health`, `grader` and `pot_size_in` come back from labeling."""

    tag_id = pxt.Column(type=pxt.Int, primary_key=True)
    species: pxt.String
    style: pxt.String
    age_years: pxt.Int
    height_cm: pxt.Float
    pot_size_in: pxt.Int
    photo: pxt.Image
    health: pxt.String | None
    grader: pxt.String | None

    pot_cm = pot_size_in * 2.54
    canopy = canopy_bbox(photo)
    thumb = pxt.Column(value=photo.resize((64, 48)), stored=False)
```

**3. Queries are functions (`app.py`).** `@pxt.query` wraps a Pixeltable query so it can be called from Python or exposed as a route:

```python
# app.py
@pxt.query
def review_queue():
    """Trees that still have no health label, oldest first."""
    return (
        Specimens.where(Specimens.health == None)  # noqa: E711
        .order_by(Specimens.age_years, asc=False)
        .select(Specimens.tag_id, Specimens.species, Specimens.style, Specimens.age_years)
    )
```

## Learn more

- 🌐 Website: https://pixeltable.com
- 📚 Docs: https://docs.pixeltable.com
- 💻 Source: https://github.com/pixeltable/pixeltable (⭐ star it if Pixeltable is useful to you)
- 📦 PyPI: https://pypi.org/project/pixeltable/
- 🧩 More example apps: https://pierrebrunelle.github.io/awesome-pixeltable-apps/

**[More Pixeltable example apps →](https://pierrebrunelle.github.io/awesome-pixeltable-apps/)**

---

<sub>Built as part of a daily series of Pixeltable example apps · Pixeltable 0.7.26 · Python, incremental computed columns · Licensed under Apache-2.0.</sub>
