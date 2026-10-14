"""POST queued thumbnails to Figma MCP upload URLs.

Usage: python3 post.py [--slice START:END] UUID [UUID ...]
       python3 post.py --slice START:END --status
Each UUID is consumed by the next pending manifest item. Progress is kept in
progress.json so the run can resume after failures.
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = Path(__file__).parent
ORDER = ["compact_full_field", "split_regions", "layered_bands", "edge_channels",
         "central_mass", "open_center", "stair_step", "asymmetric", "untagged"]
URL = "https://mcp.figma.com/mcp/upload/{}/submit?scaleMode=FILL&currentPageId=0%3A1"


def queue():
    rows = json.loads((BASE / "manifest.json").read_text())
    rows.sort(key=lambda r: (r["game"], ORDER.index(r["primary"]), r["level"]))
    return rows


def layer_name(r):
    return f"{r['game']}__{r['primary']}__{r['level']:05d}"


def post(args):
    uuid, r = args
    name = layer_name(r)
    out = subprocess.run(
        ["curl", "-s", "--max-time", "120", "-X", "POST", "-F",
         f"file=@{r['thumb']};type=image/jpeg;filename={name}.jpg", URL.format(uuid)],
        capture_output=True, text=True)
    try:
        res = json.loads(out.stdout)
    except json.JSONDecodeError:
        res = {"success": False, "raw": out.stdout[:200]}
    return name, res


def load_done():
    done = {}
    for p in BASE.glob("progress*.json"):
        done.update(json.loads(p.read_text()))
    return done


def main():
    args = sys.argv[1:]
    start, end, tag = 0, None, ""
    if args and args[0] == "--slice":
        a, b = args[1].split(":")
        start, end, tag = int(a), int(b), f"-{a}-{b}"
        args = args[2:]
    prog_path = BASE / f"progress{tag}.json"
    prog = json.loads(prog_path.read_text()) if prog_path.exists() else {}
    done = load_done()
    pending = [r for r in queue()[start:end] if layer_name(r) not in done]
    if args == ["--status"]:
        print(f"remaining_in_slice={len(pending)}")
        return
    uuids = args
    jobs = list(zip(uuids, pending))
    with ThreadPoolExecutor(16) as ex:
        results = list(ex.map(post, jobs))
    failed = 0
    for name, res in results:
        if res.get("success"):
            prog[name] = res["placedOnNodeId"]
        else:
            failed += 1
            print("FAIL", name, res)
    prog_path.write_text(json.dumps(prog))
    print(f"posted={len(results) - failed} failed={failed} done={len(prog)} "
          f"remaining={len(pending) - len(results) + failed}")


if __name__ == "__main__":
    main()
