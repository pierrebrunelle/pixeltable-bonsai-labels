"""Export -> edit externally -> re-import -> diff, for the bonsai nursery's health labels.

    python roundtrip.py seed                         # load data/specimens.csv (+ photos)
    python roundtrip.py export csv|json|parquet|coco|pytorch
    python roundtrip.py grade output/export-csv/specimens.csv data/edited/batch-1.csv [--typo]
    python roundtrip.py apply data/edited/batch-1.csv [--skip-lossy]
    python roundtrip.py diff 2 4                     # field changes between two Specimens versions
    python roundtrip.py undo                         # revert the last applied batch
    python roundtrip.py report                       # review queue, label counts, batch log -> output/labels.md

Point BONSAI_NS at a hosted database (pxt://<org>:<db>/bonsai) to run the same loop against
Pixeltable Cloud. The COCO and PyTorch exports read the local catalog only.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import random
import shutil
import sys
from pathlib import Path

import os

import pixeltable as pxt

import app

APP = Path(__file__).parent
DATA = APP / 'data'
OUT = APP / 'output'
NS = os.environ.get('BONSAI_NS', 'bonsai')

# Columns a grader may change; everything else in an edited file is ignored.
EDITABLE = ['species', 'style', 'height_cm', 'pot_size_in', 'health', 'grader']
EXPORT_COLS = ['tag_id', 'species', 'style', 'age_years', 'height_cm', 'pot_size_in', 'health', 'grader']
# Types for the re-import: without them a column of whole numbers with one blank cell comes
# back as Float, and an all-blank label column has no type at all.
IMPORT_TYPES = {
    'tag_id': pxt.Int,
    'species': pxt.String,
    'style': pxt.String,
    'age_years': pxt.Int,
    'height_cm': pxt.Float,
    'pot_size_in': pxt.Int,
    'health': pxt.String | None,
    'grader': pxt.String | None,
}
HEALTH = ['healthy', 'needs repot', 'pest watch', 'root rot risk']

app.TableModel.bind_all(NS)
S, B = app.Specimens, app.LabelBatches


def version() -> int:
    return S.get_versions(n=1)[0]['version']


def cmd_seed() -> None:
    with open(DATA / 'specimens.csv', newline='') as f:
        rows = [
            {
                'tag_id': int(r['tag_id']),
                'species': r['species'],
                'style': r['style'],
                'age_years': int(r['age_years']),
                'height_cm': float(r['height_cm']),
                'pot_size_in': int(r['pot_size_in']),
                'photo': str(APP / r['photo']),
            }
            for r in csv.DictReader(f)
        ]
    status = S.insert(rows, if_exists='ignore')
    print(f'seed: {status.row_count_stats.inserted_rows} inserted, {status.row_count_stats.skipped_rows} skipped')


def cmd_export(fmt: str) -> None:
    dest = OUT / f'export-{fmt}'
    dest.mkdir(parents=True, exist_ok=True)
    q = S.order_by(S.tag_id).select(*[getattr(S, c) for c in EXPORT_COLS])
    if fmt == 'csv':
        pxt.io.export_csv(q, dest / 'specimens.csv')
    elif fmt == 'json':
        pxt.io.export_json(q, dest / 'specimens.jsonl')
    elif fmt == 'parquet':
        pxt.io.export_parquet(q, dest / 'specimens.parquet', if_exists='replace')
    elif fmt == 'coco':
        # One box per tree: the canopy found in the photo, labelled with the tree's style.
        coco = S.order_by(S.tag_id).select(
            {'image': S.photo, 'annotations': [{'bbox': S.canopy, 'category': S.style}]}
        )
        path = coco.to_coco_dataset()
        shutil.copytree(path.parent, dest / 'coco', dirs_exist_ok=True)
        d = json.loads((dest / 'coco' / 'data.json').read_text())
        print(f"coco: {len(d['images'])} images, {len(d['annotations'])} boxes, {len(d['categories'])} categories")
    elif fmt == 'pytorch':
        from torch.utils.data import DataLoader

        labelled = S.where(S.health != None).order_by(S.tag_id)  # noqa: E711
        ds = labelled.select(img=S.photo.resize((64, 48)), health=S.health, pot=S.pot_size_in).to_pytorch_dataset()
        n = 0
        for batch in DataLoader(ds, batch_size=4):
            n += len(batch['health'])
            print(f"pytorch batch: img {tuple(batch['img'].shape)}, pot {batch['pot'].tolist()}, health {batch['health']}")
        print(f'pytorch: {n} labelled rows')
        return
    else:
        sys.exit(f'unknown format {fmt}')
    print(f'export {fmt}: {sorted(p.name for p in dest.iterdir())}')


def cmd_grade(src: str, dst: str, typo: bool) -> None:
    """Stand-in for a grader editing the exported CSV in a spreadsheet."""
    rng = random.Random(Path(dst).stem)
    with open(src, newline='') as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        if not r['health'] and rng.random() < 0.7:
            r['health'] = rng.choice(HEALTH)
            r['grader'] = rng.choice(['Aiko', 'Ben', 'Carmen'])
            if r['health'] == 'needs repot':
                r['pot_size_in'] = str(int(r['pot_size_in']) + 2)
    if typo:
        # A re-measured pot typed as 9.5 inches: pots come in whole inches.
        rows[2]['pot_size_in'] = '9.5'
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    with open(dst, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"grade: wrote {dst} ({sum(1 for r in rows if r['health'])} labelled rows)")


def stage(path: Path, batch_id: str) -> pxt.Table:
    name = f'{NS}/staging_{batch_id}'
    pxt.drop_table(name, if_not_exists='ignore')
    loader = {'.csv': pxt.io.import_csv, '.jsonl': pxt.io.import_json, '.json': pxt.io.import_json}[path.suffix]
    if path.suffix == '.csv':
        return loader(name, str(path), schema_overrides=IMPORT_TYPES, primary_key='tag_id')
    return loader(name, str(path), schema_overrides=IMPORT_TYPES, primary_key='tag_id')


def cmd_apply(file: str, skip_lossy: bool) -> None:
    path = Path(file)
    batch_id = path.stem.replace('-', '_')
    if B.where(B.batch_id == batch_id).count() > 0:
        print(f'apply: batch {batch_id} already applied')
        return
    rejected = None
    try:
        staged = stage(path, batch_id)
    except pxt.Error as e:
        # Pixeltable refuses a non-integral value for an Int column instead of truncating it.
        rejected = {'error': str(e).splitlines()[0]}
        print(f'apply: refused {path.name}: {rejected["error"]}')
        # The refused import still leaves an empty staging table behind; remove it.
        pxt.drop_table(f'{NS}/staging_{batch_id}', if_not_exists='ignore')
        if not skip_lossy:
            sys.exit(3)
        with open(path, newline='') as f:
            rows = list(csv.DictReader(f))
        keep = [r for r in rows if float(r['pot_size_in']).is_integer()]
        rejected['tag_ids'] = [int(r['tag_id']) for r in rows if r not in keep]
        cleaned = OUT / 'cleaned' / path.name
        cleaned.parent.mkdir(parents=True, exist_ok=True)
        with open(cleaned, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(keep)
        print(f"apply: skipping tag(s) {rejected['tag_ids']}, staging the other {len(keep)} rows")
        staged = stage(cleaned, batch_id)

    # Pair each staged row with the live row of the same tag (one join), then keep the fields that differ.
    pairs = (
        staged.join(S, on=staged.tag_id == S.tag_id)
        .order_by(staged.tag_id)
        .select(
            staged.tag_id,
            *[getattr(staged, c) for c in EDITABLE],
            **{f'live_{c}': getattr(S, c) for c in EDITABLE},
        )
        .collect()
    )
    changes = []
    for r in pairs:
        if any(r[c] != r[f'live_{c}'] for c in EDITABLE):
            # batch_update() needs the same columns in every row, so send all editable fields.
            changes.append({'tag_id': r['tag_id'], **{c: r[c] for c in EDITABLE}})
    st = pairs
    before = version()
    if changes:
        S.batch_update(changes)
    after = version()
    B.insert(
        batch_id=batch_id,
        file_name=path.name,
        file_format=path.suffix.lstrip('.'),
        rows_in=len(st),
        rows_changed=len(changes),
        rejected=rejected,
        version_before=before,
        version_after=after,
        applied_at=dt.datetime.now(dt.timezone.utc),
    )
    pxt.drop_table(staged)
    print(f'apply: {batch_id}: {len(st)} rows in, {len(changes)} changed, Specimens v{before} -> v{after}')


def cmd_diff(va: int, vb: int) -> None:
    def rows(v: int) -> dict[int, dict]:
        t = pxt.get_table(f'{NS}/specimens:{v}')  # read-only handle on version v
        return {r['tag_id']: r for r in t.select(*[getattr(t, c) for c in ['tag_id', *EDITABLE]]).collect()}

    # Rows of the two versions are matched by tag in Python.
    a, b = rows(va), rows(vb)
    n = 0
    for tag in sorted(set(a) | set(b)):
        ra, rb = a.get(tag), b.get(tag)
        if ra is None or rb is None:
            print(f'{tag}: {"added" if ra is None else "removed"}')
            n += 1
            continue
        for c in EDITABLE:
            if ra[c] != rb[c]:
                print(f'{tag}: {c}: {ra[c]!r} -> {rb[c]!r}')
                n += 1
    print(f'diff v{va} -> v{vb}: {n} changes')


def cmd_undo() -> None:
    last = B.order_by(B.applied_at, asc=False).limit(1).collect()
    if len(last) == 0:
        print('undo: nothing applied')
        return
    row = last[0]
    if version() != row['version_after'] or row['version_after'] == row['version_before']:
        sys.exit(f"undo: Specimens is at v{version()}, batch {row['batch_id']} ended at v{row['version_after']}")
    pxt.get_table(f'{NS}/specimens').revert()  # the bound model class has no revert()
    B.delete(where=B.batch_id == row['batch_id'])
    print(f"undo: reverted batch {row['batch_id']}; Specimens back to v{version()}")


def cmd_report() -> None:
    queue = pxt.eval_udf(app.review_queue)
    counts = pxt.eval_udf(app.label_counts)
    log = pxt.eval_udf(app.batch_log)
    lines = ['# Bonsai labels', '', '## Label counts', '']
    lines += [f"- {r['health']}: {r['n']}" for r in counts]
    lines += ['', f'## Review queue ({len(queue)} trees)', '']
    lines += [f"- {r['tag_id']} {r['species']} ({r['style']}, {r['age_years']} y)" for r in queue]
    lines += ['', '## Batches', '']
    lines += [
        f"- {r['batch_id']} ({r['file_format']}): {r['rows_in']} in, {r['rows_changed']} changed, "
        f"v{r['version_before']} -> v{r['version_after']}"
        for r in log
    ]
    OUT.mkdir(exist_ok=True)
    (OUT / 'labels.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))


def main(argv: list[str]) -> None:
    cmd, args = (argv[0], argv[1:]) if argv else ('help', [])
    if cmd == 'seed':
        cmd_seed()
    elif cmd == 'export':
        cmd_export(args[0])
    elif cmd == 'grade':
        cmd_grade(args[0], args[1], '--typo' in args)
    elif cmd == 'apply':
        cmd_apply(args[0], '--skip-lossy' in args)
    elif cmd == 'diff':
        cmd_diff(int(args[0]), int(args[1]))
    elif cmd == 'undo':
        cmd_undo()
    elif cmd == 'report':
        cmd_report()
    else:
        print(__doc__)


if __name__ == '__main__':
    main(sys.argv[1:])
