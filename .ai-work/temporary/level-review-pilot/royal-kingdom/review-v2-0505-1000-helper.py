import hashlib, json, sys
import re
from pathlib import Path

BASE = Path('.ai-work/temporary/level-review-pilot/royal-kingdom')
INDEX = BASE / 'sheets-20261009/index.json'
OUTPUT = BASE / 'review-v2-0505-1000.jsonl'
VISUAL = {
 'A': (['compact_full_field'], 'A single compact, mostly contiguous match field is visible; scattered internal blockers do not divide the outer playable boundary.'),
 'B': (['layered_bands'], 'The visible match field is organized in distinct horizontal rows or bands of pieces and blockers.'),
 'C': (['asymmetric'], 'The playable cells form an uneven, one-sided outline; this describes the outer play area rather than an internal blocker edge.'),
 'D': (['split_regions'], 'Two or more visibly separated matchable areas are present; the separation is in playable cells, not inferred from blocker placement alone.'),
 'E': (['central_mass'], 'A large internal obstacle or covered area dominates the center, with visible matchable cells remaining around it.'),
 'F': (['edge_channels'], 'Matchable cells are concentrated in narrow lanes along one or more outer edges of the field.'),
 'G': (['stair_step'], 'The outer playable-cell boundary itself follows a visible stepped progression; an internal stepped blocker edge is not counted.'),
 'H': (['open_center'], 'The center of the playable field is visibly open, with play areas or blockers around the perimeter.'),
 '?': ([], 'The screenshot is visible, but the matchable-cell boundary cannot be determined confidently from the displayed board.'),
}

def checkpoint(sheet_name):
    assert len(sys.argv) == 3 and sys.argv[1] == sheet_name
    idx = json.loads(INDEX.read_text())
    sh = next(s for s in idx['sheets'] if s['sheet'] == sheet_name)
    rows = [r for r in sh['records'] if 505 <= r['level'] <= 1000]
    codes = sys.argv[2]
    assert len(rows) == len(codes), (sheet_name, len(rows), len(codes))
    current = OUTPUT.read_text().splitlines() if OUTPUT.exists() else []
    saved_levels = {json.loads(line)['level'] for line in current}
    payload = []
    for rec, code in zip(rows, codes):
        assert rec['level'] not in saved_levels
        image = Path(rec['image'])
        assert image.is_file()
        digest = hashlib.sha256(image.read_bytes()).hexdigest()
        assert digest == rec['sha256']
        tags, observation = VISUAL[code]
        partial = code == '?'
        obj = {
            'schema_version': 2,
            'game': 'royal-kingdom',
            'level': rec['level'],
            'review_status': 'needs_review' if partial else 'candidate',
            'inspection_status': 'partial' if partial else 'reviewed',
            'image_path': rec['image'],
            'image_sha256': digest,
            'sheet_path': str(BASE / 'sheets-20261009' / sheet_name),
            'cell': rec['cell'],
            'geometry_tags': tags,
            'observation': observation,
            'occlusion': 'unknown' if partial else 'none',
            'confidence': 'low' if partial else 'medium',
            'verified_difficulty': 'unknown',
            'verified_strategy': 'unknown',
            'verified_evidence': [],
            'difficulty_hypothesis': None,
            'strategy_hypothesis': None,
            'review_note': 'The gameplay board geometry needs follow-up; no gameplay video or direct difficulty label was available.' if partial else 'Initial board geometry only; no gameplay video or direct difficulty label was available.'
        }
        payload.append(json.dumps(obj, ensure_ascii=False, separators=(',', ':')))
    with OUTPUT.open('a', encoding='utf-8') as f:
        f.write('\n'.join(payload) + '\n')
        f.flush()
    print(f'Checkpointed {sheet_name}: {len(payload)} rows; total {len(current) + len(payload)}')

if __name__ == '__main__':
    checkpoint(sys.argv[1])
