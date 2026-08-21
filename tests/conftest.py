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


# ---------------------------------------------------------------------------
# Dem so test that su thu thap duoc, cho test_so_lieu_tai_lieu.py doi chieu
# voi con so ghi trong tai lieu.
#
# Vi sao khong dem bang AST: 15 cho dung @pytest.mark.parametrize, nen 267 ham
# `def test_*` no ra 329 test. Chi pytest moi biet con so that.
#
# Vi sao co co `DAY_DU`: chay `pytest tests/test_mot_file.py` cung goi hook
# nay, luc do so item la 3 chu khong phai 329. So sanh voi tai lieu se do oan.
# ---------------------------------------------------------------------------

SO_TEST_THU_THAP = None
THU_THAP_DAY_DU = False


def pytest_collection_modifyitems(session, config, items):
    global SO_TEST_THU_THAP, THU_THAP_DAY_DU
    SO_TEST_THU_THAP = len(items)

    # "Day du" = khong chi dinh file/node cu the nao. `pytest`, `pytest tests`,
    # `pytest tests/` deu tinh la day du; `pytest tests/test_x.py` thi khong.
    args = [a for a in config.args if not a.startswith("-")]
    THU_THAP_DAY_DU = all(
        Path(a.split("::")[0]).resolve() in (ROOT, ROOT / "tests")
        for a in args
    ) if args else True
