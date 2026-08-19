"""
Kiem thu crawler - KHONG goi mang.

Trong tam cua bo test nay khong phai "crawler chay duoc" ma la
"crawler khong bao gio bia du lieu". Cu the:

  - trang loi HTTP  -> status failed, khong co truong du lieu nao duoc dien
  - noi dung qua ngan -> status empty, khong bu bang gia tri mac dinh
  - robots.txt cam  -> status robots_disallowed, khong tai
  - khong co title  -> title = None, khong doan

Xem quy chuan v2.0 muc 23.1 nguyen tac 3.
"""

import json

import pytest

import crawl
from robots import RobotsDecision


# ----------------------------------------------------------------------
# Do gia
# ----------------------------------------------------------------------
class FakeResponse:
    def __init__(self, content=b"", status_code=200, content_type="text/html"):
        self.content = content
        self.status_code = status_code
        self.headers = {"Content-Type": content_type}


class FakeSession:
    """Session gia tra ve mot phan hoi da dinh san, hoac nem loi."""

    def __init__(self, response=None, exc=None):
        self.response = response
        self.exc = exc
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append(url)
        if self.exc is not None:
            raise self.exc
        return self.response


class FakeRobots:
    def __init__(self, allowed=True, reason="test", crawl_delay=None):
        self.decision = RobotsDecision(allowed=allowed, reason=reason,
                                       crawl_delay=crawl_delay)
        self.checked = []

    def check(self, url):
        self.checked.append(url)
        return self.decision


class NoWaitThrottle:
    """Khong ngu that trong test."""

    def __init__(self):
        self.calls = []

    def wait(self, url, override=None):
        self.calls.append((url, override))


SRC = {
    "id": "test_nguon",
    "crop": "ca_chua",
    "region": "dong_bang_song_hong",
    "publisher": "Nguon kiem thu",
    "url": "https://vi.du/ky-thuat-trong-ca-chua",
}


def make_pdf(text: str) -> bytes:
    """Tao mot file PDF toi thieu hop le, tinh dung offset xref.

    Dung de kiem chung DEC-027 (crawler doc duoc PDF) ma khong can them
    phu thuoc chi de sinh fixture.
    """
    content = "BT /F1 12 Tf 20 100 Td (" + text + ") Tj ET"
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] "
        "/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        "<< /Length " + str(len(content)) + " >>\nstream\n" + content + "\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += (str(i) + " 0 obj\n" + body + "\nendobj\n").encode("latin-1")

    xref_at = len(out)
    out += ("xref\n0 " + str(len(objects) + 1) + "\n").encode("latin-1")
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += (str(off).zfill(10) + " 00000 n \n").encode("latin-1")
    out += ("trailer\n<< /Size " + str(len(objects) + 1) +
            " /Root 1 0 R >>\nstartxref\n" + str(xref_at) + "\n%%EOF\n").encode("latin-1")
    return bytes(out)


# ----------------------------------------------------------------------
# Tach van ban
# ----------------------------------------------------------------------
def test_html_to_text_loai_bo_boilerplate():
    html = b"""<html><head><title>T</title>
        <style>body{color:red}</style><script>alert(1)</script></head>
        <body><nav>Trang chu | Lien he</nav>
        <header>Banner</header>
        <p>Ky thuat trong ca chua</p>
        <footer>Ban quyen</footer></body></html>"""
    text = crawl.html_to_text(html)
    assert "Ky thuat trong ca chua" in text
    for rac in ("alert(1)", "color:red", "Trang chu", "Banner", "Ban quyen"):
        assert rac not in text


def test_html_title_lay_duoc_tu_the_title():
    html = b"<html><head><title>  Quy trinh trong dua chuot  </title></head><body>x</body></html>"
    assert crawl.html_title(html) == "Quy trinh trong dua chuot"


def test_html_title_lui_ve_h1():
    html = b"<html><head></head><body><h1>Ky thuat trong lua</h1></body></html>"
    assert crawl.html_title(html) == "Ky thuat trong lua"


def test_html_title_khong_co_thi_tra_none_chu_khong_doan():
    """Khong co title thi de None. Khong duoc suy ra tu URL hay tu noi dung."""
    html = b"<html><head></head><body><p>chi co doan van</p></body></html>"
    assert crawl.html_title(html) is None


# ----------------------------------------------------------------------
# Nhan dien va doc PDF (DEC-027)
# ----------------------------------------------------------------------
def test_is_pdf_theo_content_type():
    assert crawl.is_pdf("https://vi.du/a", "application/pdf", None)


def test_is_pdf_theo_duoi_file():
    assert crawl.is_pdf("https://vi.du/quy-trinh.PDF", "text/html", None)


def test_is_pdf_theo_chu_ky_byte():
    assert crawl.is_pdf("https://vi.du/tai-ve", None, b"%PDF-1.7 ...")


def test_is_pdf_tra_false_voi_html():
    assert not crawl.is_pdf("https://vi.du/a.html", "text/html", b"<html>")


def test_pdf_to_text_doc_duoc_noi_dung():
    pdf = make_pdf("Do am dat thich hop cho ca chua")
    text, _title = crawl.pdf_to_text(pdf)
    assert "ca chua" in text.lower()


# ----------------------------------------------------------------------
# Gian nhip theo ten mien
# ----------------------------------------------------------------------
def test_throttle_khong_cho_o_lan_dau():
    import time as _time

    throttle = crawl.DomainThrottle(delay=5.0)
    start = _time.monotonic()
    throttle.wait("https://a.vn/x")
    assert _time.monotonic() - start < 1.0


def test_throttle_tinh_rieng_tung_ten_mien():
    import time as _time

    throttle = crawl.DomainThrottle(delay=5.0)
    throttle.wait("https://a.vn/x")
    start = _time.monotonic()
    throttle.wait("https://b.vn/y")   # ten mien khac -> khong phai cho
    assert _time.monotonic() - start < 1.0


# ----------------------------------------------------------------------
# Trang thai - phan quan trong nhat
# ----------------------------------------------------------------------
def test_http_404_thi_that_bai_va_khong_bia_du_lieu():
    session = FakeSession(FakeResponse(b"", status_code=404))
    rec = crawl.crawl_one(SRC, session, FakeRobots(), NoWaitThrottle())

    assert rec["status"] == crawl.STATUS_FAILED
    assert rec["http_status"] == 404
    # Khong duoc co bat ky truong du lieu nao duoc dien thay
    for truong in ("sha256", "text_file", "raw_file", "text_length", "title"):
        assert truong not in rec


def test_loi_mang_thi_that_bai():
    import requests as _requests

    session = FakeSession(exc=_requests.ConnectionError("khong ket noi duoc"))
    rec = crawl.crawl_one(SRC, session, FakeRobots(), NoWaitThrottle())

    assert rec["status"] == crawl.STATUS_FAILED
    assert rec["http_status"] is None
    assert "ConnectionError" in rec["error"]
    assert "sha256" not in rec


def test_noi_dung_qua_ngan_thi_empty_va_khong_bu_gi():
    html = b"<html><body><p>ngan</p></body></html>"
    session = FakeSession(FakeResponse(html))
    rec = crawl.crawl_one(SRC, session, FakeRobots(), NoWaitThrottle())

    assert rec["status"] == crawl.STATUS_EMPTY
    assert rec["text_length"] < crawl.MIN_TEXT_LEN
    assert "sha256" not in rec
    assert "text_file" not in rec


def test_robots_cam_thi_khong_tai():
    session = FakeSession(FakeResponse(b"<html>" + b"x" * 500 + b"</html>"))
    robots = FakeRobots(allowed=False, reason="robots.txt cam duong dan nay")
    rec = crawl.crawl_one(SRC, session, robots, NoWaitThrottle())

    assert rec["status"] == crawl.STATUS_ROBOTS
    assert session.calls == []          # tuyet doi khong duoc goi request
    assert "sha256" not in rec


def test_tai_thanh_cong_ghi_du_bang_chung(tmp_path, monkeypatch):
    monkeypatch.setattr(crawl, "RAW", tmp_path / "raw")
    monkeypatch.setattr(crawl, "TEXT", tmp_path / "text")
    crawl.RAW.mkdir(parents=True)
    crawl.TEXT.mkdir(parents=True)

    body = "Ky thuat trong ca chua. " * 30
    html = ("<html><head><title>Ca chua</title></head><body><p>"
            + body + "</p></body></html>").encode("utf-8")
    session = FakeSession(FakeResponse(html))

    rec = crawl.crawl_one(SRC, session, FakeRobots(), NoWaitThrottle())

    assert rec["status"] == crawl.STATUS_OK
    assert rec["doc_type"] == "html"
    assert rec["title"] == "Ca chua"
    assert len(rec["sha256"]) == 64
    assert rec["text_length"] >= crawl.MIN_TEXT_LEN
    # Bang chung goc phai nam tren dia
    assert (crawl.RAW / "test_nguon.html").exists()
    assert (crawl.TEXT / "test_nguon.txt").exists()
    # Metadata goc phai duoc giu nguyen de truy nguon
    assert rec["url"] == SRC["url"]
    assert rec["crop"] == SRC["crop"]


def test_pdf_tai_thanh_cong_duoc_ghi_dung_doc_type(tmp_path, monkeypatch):
    monkeypatch.setattr(crawl, "RAW", tmp_path / "raw")
    monkeypatch.setattr(crawl, "TEXT", tmp_path / "text")
    crawl.RAW.mkdir(parents=True)
    crawl.TEXT.mkdir(parents=True)

    pdf = make_pdf("Quy trinh ky thuat trong ca chua. " * 12)
    session = FakeSession(FakeResponse(pdf, content_type="application/pdf"))

    rec = crawl.crawl_one(SRC, session, FakeRobots(), NoWaitThrottle())

    assert rec["status"] == crawl.STATUS_OK
    assert rec["doc_type"] == "pdf"
    assert (crawl.RAW / "test_nguon.pdf").exists()


# ----------------------------------------------------------------------
# Nguyen tac tong quat
# ----------------------------------------------------------------------
def test_script_khong_chua_so_lieu_nong_hoc():
    """Nguyen tac 1: khong hard-code so lieu nong hoc trong code.

    Test nay khong the chung minh tuyet doi, nhung chan duoc truong hop de gap
    nhat: dat san mot khoang pH / do am / nhiet do trong ma nguon.
    """
    import re
    from pathlib import Path

    nguon = Path(crawl.__file__).read_text(encoding="utf-8")
    # bo phan docstring/comment de giam bao dong gia
    dong_ma = [ln for ln in nguon.splitlines() if not ln.strip().startswith("#")]
    ma = "\n".join(dong_ma).lower()

    for tu_khoa in ("ph ", "do am", "nhiet do", "ec ", "nang suat"):
        for match in re.finditer(re.escape(tu_khoa), ma):
            doan = ma[match.start(): match.start() + 60]
            assert not re.search(r"\d+([.,]\d+)?\s*(-|den|to)\s*\d", doan), (
                "Nghi ngo co so lieu nong hoc hard-code gan '" + tu_khoa + "': " + doan
            )


# ----------------------------------------------------------------------
# Gop manifest khi chay mot phan
# ----------------------------------------------------------------------
def test_gop_manifest_giu_ban_ghi_cu():
    """Chay --only khong duoc xoa bang chung cua cac nguon khac.

    Loi nay da xay ra that: mot lan chay --only hai nguon da ghi de manifest
    va xoa 80 ban ghi truoc do.
    """
    cu = [{"id": "a", "status": "ok"}, {"id": "b", "status": "failed"}]
    moi = [{"id": "c", "status": "ok"}]
    gop = crawl.gop_manifest(cu, moi)
    assert {r["id"] for r in gop} == {"a", "b", "c"}


def test_gop_manifest_ban_ghi_moi_thay_ban_cu_cung_id():
    cu = [{"id": "a", "status": "failed"}, {"id": "b", "status": "ok"}]
    moi = [{"id": "a", "status": "ok"}]
    gop = crawl.gop_manifest(cu, moi)
    theo_id = {r["id"]: r for r in gop}
    assert len(gop) == 2
    assert theo_id["a"]["status"] == "ok"      # ban moi thang
    assert theo_id["b"]["status"] == "ok"      # ban cu con nguyen


def test_gop_manifest_khong_co_ban_cu():
    moi = [{"id": "a", "status": "ok"}]
    assert crawl.gop_manifest([], moi) == moi
