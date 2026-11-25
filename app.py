"""Bonsai nursery label round-trip, built with Pixeltable.

`Specimens` is the nursery inventory: one tree per row with its tag, species, style, age,
height, pot size and a photo. Graders label each tree's health outside Pixeltable (in a
spreadsheet or a labeling tool), so the table is exported, edited elsewhere and imported
back. Computed columns derive the canopy bounding box from the photo (used for the COCO
export) and the pot size in centimetres.

`LabelBatches` records every re-import: the file, its format, how many rows changed, the
rows that were rejected, and the table versions before and after the batch, so any batch
can be diffed or reverted.

The `@pxt.query` functions are the review queue, the label distribution and the batch log.
roundtrip.py drives the export -> edit -> re-import -> diff loop. No HTTP router.

    python make_data.py
    pxt schema update app.py bonsai
    python roundtrip.py seed
    python roundtrip.py export csv
"""

from __future__ import annotations

import pixeltable as pxt

from udfs import canopy_bbox

TableModel = pxt.model_base()


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


class LabelBatches(TableModel, name='label_batches'):
    """One re-imported label file and the Specimens versions around it."""

    batch_id = pxt.Column(type=pxt.String, primary_key=True)
    file_name: pxt.String
    file_format: pxt.String
    rows_in: pxt.Int
    rows_changed: pxt.Int
    rejected: pxt.Json | None
    version_before: pxt.Int
    version_after: pxt.Int
    applied_at: pxt.Timestamp


@pxt.query
def review_queue():
    """Trees that still have no health label, oldest first."""
    return (
        Specimens.where(Specimens.health == None)  # noqa: E711
        .order_by(Specimens.age_years, asc=False)
        .select(Specimens.tag_id, Specimens.species, Specimens.style, Specimens.age_years)
    )


@pxt.query
def label_counts():
    """How many trees carry each health label."""
    return (
        Specimens.where(Specimens.health != None)  # noqa: E711
        .group_by(Specimens.health)
        .select(Specimens.health, n=pxt.functions.count(Specimens.tag_id))
        .order_by(Specimens.health)
    )


@pxt.query
def batch_log():
    """Every applied label batch, newest first."""
    return LabelBatches.order_by(LabelBatches.applied_at, asc=False).select(
        LabelBatches.batch_id,
        LabelBatches.file_format,
        LabelBatches.rows_in,
        LabelBatches.rows_changed,
        LabelBatches.version_before,
        LabelBatches.version_after,
    )
