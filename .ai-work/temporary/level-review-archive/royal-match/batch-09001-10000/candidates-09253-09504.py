import hashlib
import json
from pathlib import Path

BASE = Path('.ai-work/temporary/level-review-archive/royal-match/batch-09001-10000')
INDEX = BASE / 'sheets/index.json'
OUTPUT = BASE / 'candidates-09253-09504.jsonl'
CHECKPOINT = BASE / 'candidates-09253-09504-checkpoint.json'
SHEET_ROOT = '.ai-work/temporary/level-review-archive/royal-match/batch-09001-10000/sheets/'


def load_checkpoint():
    if CHECKPOINT.exists():
        return json.loads(CHECKPOINT.read_text())
    return {'schema_version': 2, 'game': 'royal-match', 'range': [9253, 9504],
            'completed_sheets': [], 'reviewed': {}, 'last_committed_level': None}


def commit_sheet(sheet_name):
    state = load_checkpoint()
    if sheet_name in state['completed_sheets']:
        return
    notes = state['reviewed']
    index = json.loads(INDEX.read_text())
    sheet = next((s for s in index['sheets'] if s['sheet'] == sheet_name), None)
    if sheet is None:
        raise ValueError(f'Unknown sheet: {sheet_name}')
    records = [r for r in sheet['records'] if 9253 <= r['level'] <= 9504]
    if len(records) != 12 or any(str(r['level']) not in notes for r in records):
        raise ValueError(f'Expected 12 reviewed notes for {sheet_name}')
    existing = {}
    if OUTPUT.exists():
        for line in OUTPUT.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                existing[row['level']] = row
    additions = []
    for src in records:
        level = src['level']
        if level in existing:
            continue
        note = notes[str(level)]
        missing = src.get('status') == 'missing' or not src.get('image') or not src.get('sha256')
        row = {
            'schema_version': 2,
            'game': 'royal-match',
            'level': level,
            'review_status': 'needs_review',
            'inspection_status': 'missing' if missing else note.get('inspection_status', 'reviewed'),
            'image_path': None if missing else src['image'],
            'image_sha256': None if missing else src['sha256'],
            'sheet_path': None if missing else SHEET_ROOT + sheet_name,
            'cell': None if missing else src['cell'],
            'geometry_tags': [] if missing else note['geometry_tags'],
            'observation': note['observation'],
            'occlusion': 'unknown' if missing else note.get('occlusion', 'none'),
            'confidence': 'unknown' if missing else note['confidence'],
            'verified_difficulty': 'unknown',
            'verified_strategy': 'unknown',
            'verified_evidence': [],
            'difficulty_hypothesis': None,
            'strategy_hypothesis': None,
            'review_note': note.get('review_note', 'Difficulty and strategy remain unverified; no cited local evidence.')
        }
        if missing:
            row['observation'] = 'Source image is absent from the local sheet index; no visual claim recorded.'
            row['review_note'] = 'Missing source; obtain the original image before visual review.'
        additions.append(row)
    with OUTPUT.open('a') as out:
        for row in additions:
            out.write(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n')
    state['completed_sheets'].append(sheet_name)
    state['last_committed_level'] = max(r['level'] for r in records)
    state['committed_count'] = len(existing) + len(additions)
    state['output_sha256'] = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    CHECKPOINT.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
    print(f'Committed {sheet_name}: {len(additions)} new rows; total {state["committed_count"]}.')


if __name__ == '__main__':
    import sys
    commit_sheet(sys.argv[1])
