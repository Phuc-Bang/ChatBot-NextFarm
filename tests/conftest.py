"""Cau hinh pytest chung.

Thu muc crawler/ khong phai package nen phai them vao sys.path de import duoc
crawl.py va robots.py trong test.
"""

try:
    import sentence_transformers  # noqa: F401 - Phai import truoc de tranh segfault tren Windows
except ImportError:
    pass
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CRAWLER = ROOT / "crawler"
EVALUATION = ROOT / "evaluation"

for path in (str(ROOT), str(CRAWLER), str(EVALUATION)):
    if path not in sys.path:
        sys.path.insert(0, path)
