#!/usr/bin/env python3
"""Stream a HuggingFace arrow dataset directory (data-*.arrow) to JSONL.

The open2_official datasets are saved as HF arrow shards; run_audit.py reads
JSONL. This converts without needing the `datasets` library (pyarrow only).

  python arrow_to_jsonl.py /path/to/search_260605 --out search.jsonl --limit 2000
  python arrow_to_jsonl.py /path/to/mcp_260625    --out mcp.jsonl
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="dataset dir containing data-*.arrow (or a single .arrow)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0, help="0 = all rows")
    ap.add_argument("--add-index", default="idx", help="inject a row index under this key")
    args = ap.parse_args()

    try:
        import pyarrow as pa
    except ImportError:
        sys.exit("pyarrow required: pip install pyarrow")

    if os.path.isdir(args.src):
        shards = sorted(glob.glob(os.path.join(args.src, "data-*.arrow")))
    else:
        shards = [args.src]
    if not shards:
        sys.exit(f"no .arrow shards under {args.src}")

    n = 0
    with open(args.out, "w") as fout:
        for shard in shards:
            # HF saves arrow in IPC stream format; fall back to file format.
            try:
                reader = pa.ipc.open_stream(pa.OSFile(shard, "rb"))
                batches = iter(lambda: reader.read_next_batch(), None)
                tbls = (pa.Table.from_batches([b]) for b in _safe_stream(reader))
            except pa.lib.ArrowInvalid:
                tbls = [pa.ipc.open_file(pa.OSFile(shard, "rb")).read_all()]
            for tbl in tbls:
                for row in tbl.to_pylist():
                    if args.add_index and args.add_index not in row:
                        row[args.add_index] = n
                    fout.write(json.dumps(row, ensure_ascii=False) + "\n")
                    n += 1
                    if args.limit and n >= args.limit:
                        print(f"wrote {n} rows -> {args.out}")
                        return
    print(f"wrote {n} rows -> {args.out}")


def _safe_stream(reader):
    while True:
        try:
            b = reader.read_next_batch()
        except StopIteration:
            return
        if b is None:
            return
        yield b


if __name__ == "__main__":
    main()
