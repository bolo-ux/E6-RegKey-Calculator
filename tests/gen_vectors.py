#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate tests/vectors.json from the Python reference implementation.

The web build (index.html) must reproduce these values bit-for-bit.
The vector file is what tests/web_selftest.js checks the browser JS against.

Usage:
  python tests/gen_vectors.py          # write vectors.json
  python tests/gen_vectors.py --check  # exit 1 if vectors.json is stale
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from e6_keygen import calc  # noqa: E402

SEED = 20261018
EDGE = [
    0, 1, 7, 10, 999,
    4653170,            # 设备2 机器码
    1953915238,         # 设备1 机器码
    11160725,           # 与 MAGIC 常量同值
    99999999, 100000000,
    16777216,           # 2^24
    2147483647, 2147483648,
    4294967295,         # 2^32-1, 机器码上限
    123456789,
]
rng = random.Random(SEED)
codes = EDGE + [rng.randrange(0, 2 ** 32) for _ in range(200)]

data = {
    "generated_by": "tests/gen_vectors.py (python reference: e6_keygen.calc)",
    "seed": SEED,
    "cases": [{"mc": c, "e013": calc(c)[0], "e014": calc(c)[1]} for c in codes],
}
path = os.path.join(HERE, "vectors.json")
text = json.dumps(data, indent=1, ensure_ascii=False) + "\n"

if "--check" in sys.argv:
    current = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
    if current.replace("\r\n", "\n") != text:
        print("vectors.json is stale; run: python tests/gen_vectors.py")
        sys.exit(1)
    print("vectors.json OK (%d cases)" % len(data["cases"]))
else:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("wrote %s (%d cases)" % (path, len(data["cases"])))
