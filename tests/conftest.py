"""Cau hinh pytest chung.

Thu muc crawler/ khong phai package nen phai them vao sys.path de import duoc
crawl.py va robots.py trong test.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CRAWLER = ROOT / "crawler"

for path in (str(ROOT), str(CRAWLER)):
    if path not in sys.path:
        sys.path.insert(0, path)
