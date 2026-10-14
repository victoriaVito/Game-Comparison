import json
import pathlib
import sys

root = pathlib.Path('.ai-work/temporary/level-review-archive/royal-match/batch-09001-10000')
index = json.loads((root / 'sheets/index.json').read_text())
records = {r['level']: (sheet['sheet'], r) for sheet in index['sheets'] for r in sheet['records']}
sheet_name = sys.argv[1]
sheet_path = root / 'sheets' / sheet_name
sheet_rel = sheet_path.as_posix()
sheet_levels = {level for level, (name, _) in records.items() if name == sheet_name}
descriptors = json.load(sys.stdin)
if {d['level'] for d in descriptors} != sheet_levels:
    raise SystemExit(f'Checkpoint rows do not match sheet {sheet_name}')
rows = []
for d in sorted(descriptors, key=lambda x: x['level']):
    name, source = records[d['level']]
    missing = source['status'] == 'missing_manifest_entry'
    row = {
        'schema_version': 2,
        'game': 'royal-match',
        'level': d['level'],
        'review_status': 'needs_review',
        'inspection_status': 'missing' if missing else d.get('inspection_status', 'reviewed'),
        'image_path': None if missing else source['image'],
        'image_sha256': None if missing else source['sha256'],
        'sheet_path': sheet_rel,
        'cell': source['cell'],
        'geometry_tags': [] if missing else d.get('geometry_tags', []),
        'observation': d['observation'],
        'occlusion': 'unknown' if missing else d.get('occlusion', 'none'),
        'confidence': 'unknown' if missing else d.get('confidence', 'medium'),
        'verified_difficulty': 'unknown',
        'verified_strategy': 'unknown',
        'verified_evidence': [],
        'difficulty_hypothesis': None,
        'strategy_hypothesis': None,
        'review_note': d.get('review_note', 'No archived board image is listed in the sheet index.' if missing else '')
    }
    if missing and d.get('geometry_tags'):
        raise SystemExit(f'Missing level {d["level"]} cannot have geometry tags')
    rows.append(row)
checkpoint = root / f'candidates-09001-09252.checkpoint-{pathlib.Path(sheet_name).stem}.json'
checkpoint.write_text(json.dumps({'sheet_path': sheet_rel, 'levels': [r['level'] for r in rows], 'rows': rows}, indent=2, ensure_ascii=False) + '\n')
candidate_path = root / 'candidates-09001-09252.jsonl'
existing = {}
if candidate_path.exists():
    for line in candidate_path.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            existing[row['level']] = row
for row in rows:
    existing.setdefault(row['level'], row)
candidate_path.write_text(''.join(json.dumps(existing[level], ensure_ascii=False, separators=(',', ':')) + '\n' for level in sorted(existing)))
print(json.dumps({'sheet': sheet_name, 'checkpoint': checkpoint.name, 'saved_levels': len(rows), 'total_saved': len(existing), 'range': [min(r['level'] for r in rows), max(r['level'] for r in rows)]}))
