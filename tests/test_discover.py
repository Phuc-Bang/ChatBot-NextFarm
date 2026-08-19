"""
Kiem thu discover.py - KHONG goi mang.

Trong tam: nhan cay trong phai khop theo BIEN TU. Lan chay dau tien dung
so khop chuoi thuong nen "ma" khop ben trong "manh", gan nham nhan lua cho
mot bai ve nong thon moi. Nguoi duyet se tin vao nhan neu no thuong dung,
nen nhan sai la mot dang bia dat o buoc de xuat.
"""

import discover


# ----------------------------------------------------------------------
# Nhan dien cay trong
# ----------------------------------------------------------------------
def test_nhan_dung_lua():
    assert discover.guess_crop("Kỹ thuật gieo mạ vụ xuân") == "lua"
    assert discover.guess_crop("Quy trình canh tác lúa chất lượng cao") == "lua"
    assert discover.guess_crop("ky thuat trong lua nuoc") == "lua"


def test_nhan_dung_ca_chua():
    assert discover.guess_crop("Kỹ thuật trồng cà chua") == "ca_chua"
    assert discover.guess_crop("ky thuat trong ca chua ghep") == "ca_chua"


def test_nhan_dung_dua_chuot():
    assert discover.guess_crop("Kỹ thuật trồng dưa chuột vụ đông") == "dua_chuot"
    assert discover.guess_crop("Trồng dưa leo trong nhà màng") == "dua_chuot"


def test_khong_khop_ben_trong_tu_khac():
    """Loi da gap that: 'mạ' khop trong 'mạnh'."""
    assert discover.guess_crop("Bước chuyển mạnh mẽ trong xây dựng NTM") is None
    assert discover.guess_crop("Phát triển kinh tế từ nghề trồng nấm") is None


def test_cay_ngoai_pham_vi_tra_none():
    for tieu_de in ("Trồng lạc trái vụ", "Chăm sóc bưởi Phúc Trạch",
                    "Kỹ thuật nuôi tôm nước lợ", "Trồng nho mẫu đơn"):
        assert discover.guess_crop(tieu_de) is None


def test_nhieu_cay_trong_mot_tieu_de_thi_tra_none():
    """Khong chac thi de nguoi duyet quyet, khong tu chon mot cai."""
    assert discover.guess_crop("So sánh hiệu quả trồng lúa và cà chua") is None


# ----------------------------------------------------------------------
# Loc bai viet ky thuat
# ----------------------------------------------------------------------
def test_nhan_ra_bai_ky_thuat():
    assert discover.looks_like_article(
        "https://vi.du/khoa-hoc-ky-thuat/trong-dua-chuot-781.html",
        "Kỹ thuật trồng và chăm sóc dưa chuột")


def test_bo_qua_lien_ket_dieu_huong():
    assert not discover.looks_like_article("https://vi.du/lien-he", "Liên hệ")
    assert not discover.looks_like_article("https://vi.du/gioi-thieu", "Giới thiệu")


# ----------------------------------------------------------------------
# Nguyen tac
# ----------------------------------------------------------------------
def test_khong_co_url_nao_hard_code_ngoai_seeds():
    """Moi URL nguon phai den tu seeds.yaml / sources.yaml, khong nam trong code."""
    from pathlib import Path

    ma = Path(discover.__file__).read_text(encoding="utf-8")
    dong_ma = [ln for ln in ma.splitlines()
               if not ln.strip().startswith("#") and "vi.du" not in ln]
    noi_dung = "\n".join(dong_ma)
    assert "gov.vn" not in noi_dung


# ----------------------------------------------------------------------
# Phan trang
# ----------------------------------------------------------------------
def test_seed_khong_co_page_pattern_thi_chi_mot_trang():
    seed = {"id": "x", "url": "https://vi.du/muc/"}
    assert list(discover.page_urls(seed, max_pages=10)) == ["https://vi.du/muc/"]


def test_page_urls_sinh_dung_mau():
    seed = {"id": "x", "url": "https://vi.du/muc/",
            "page_pattern": "https://vi.du/muc/page-{page}/"}
    urls = list(discover.page_urls(seed, max_pages=3))
    assert urls == ["https://vi.du/muc/",
                    "https://vi.du/muc/page-2/",
                    "https://vi.du/muc/page-3/"]


def test_max_pages_cua_seed_khong_vuot_qua_gioi_han_dong_lenh():
    seed = {"id": "x", "url": "https://vi.du/muc/",
            "page_pattern": "https://vi.du/muc/page-{page}/", "max_pages": 100}
    assert len(list(discover.page_urls(seed, max_pages=4))) == 4


# ----------------------------------------------------------------------
# Sitemap
# ----------------------------------------------------------------------
def test_slug_text_doc_duoc_ten_cay_tu_duong_dan():
    text = discover.slug_text(
        "https://vi.du/ky-thuat/huong-dan-phong-tru-dich-hai-lua-vu-he-thu-123.html")
    assert discover.guess_crop(text) == "lua"


def test_loc_re_bat_duoc_url_trong_sitemap():
    xml = ("<urlset><url><loc>https://vi.du/a-lua.html</loc></url>"
           "<url><loc>\n  https://vi.du/b-ca-chua.html\n</loc></url></urlset>")
    assert discover.LOC_RE.findall(xml) == [
        "https://vi.du/a-lua.html", "https://vi.du/b-ca-chua.html"]


class _SitemapSession:
    """Tra ve noi dung sitemap theo URL."""

    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append(url)
        body = self.pages.get(url)
        if body is None:
            raise AssertionError("khong mong doi tai " + url)
        return type("R", (), {"content": body.encode("utf-8"),
                              "status_code": 200,
                              "headers": {"Content-Type": "application/xml"}})()


class _AllowRobots:
    def check(self, url):
        from robots import RobotsDecision
        return RobotsDecision(allowed=True, reason="test")


class _NoWait:
    def wait(self, url, override=None):
        pass


def test_sitemap_chi_giu_url_doan_duoc_cay_trong():
    """Khong loc thi mot sitemap sinh ra hang chuc nghin de xuat vo dung."""
    root = "https://vi.du/sitemap.xml"
    pages = {root: (
        "<urlset>"
        "<url><loc>https://vi.du/ky-thuat-trong-ca-chua-1.html</loc></url>"
        "<url><loc>https://vi.du/ky-thuat-nuoi-tom-2.html</loc></url>"
        "<url><loc>https://vi.du/phong-tru-dich-hai-lua-3.html</loc></url>"
        "</urlset>")}
    seed = {"id": "s", "sitemap": root}

    found, err = discover.harvest_sitemap(
        seed, _SitemapSession(pages), _AllowRobots(), _NoWait(), max_links=100)

    assert err is None
    assert {f["crop_guess"] for f in found} == {"ca_chua", "lua"}
    assert all("tom" not in f["url"] for f in found)


def test_sitemap_doc_duoc_sitemap_con():
    root = "https://vi.du/sitemap.xml"
    child = "https://vi.du/sitemaps/ngay-1.xml"
    pages = {
        root: "<sitemapindex><sitemap><loc>" + child + "</loc></sitemap></sitemapindex>",
        child: "<urlset><url><loc>https://vi.du/cham-soc-lua-xuan-9.html</loc></url></urlset>",
    }
    seed = {"id": "s", "sitemap": root, "max_sitemaps": 10}

    found, err = discover.harvest_sitemap(
        seed, _SitemapSession(pages), _AllowRobots(), _NoWait(), max_links=100)

    assert err is None
    assert len(found) == 1
    assert found[0]["crop_guess"] == "lua"
    assert found[0]["from_sitemap"] is True


def test_sitemap_bo_url_di_dang_noi_hai_dia_chi():
    """Sitemap that co muc noi hai URL vao nhau - phai bo, khong doan sua."""
    root = "https://vi.du/sitemap.xml"
    pages = {root: (
        "<urlset><url><loc>"
        "https://vi.du/muc/https://khac.vn/trong-lua-abc.html"
        "</loc></url></urlset>")}
    seed = {"id": "s", "sitemap": root}

    found, err = discover.harvest_sitemap(
        seed, _SitemapSession(pages), _AllowRobots(), _NoWait(), max_links=100)

    assert err is None
    assert found == []
