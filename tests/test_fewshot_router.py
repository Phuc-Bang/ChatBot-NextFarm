"""
Kiem thu cho tang LLM Few-Shot Intent Router (§11.3 & §40.2 Muc 9).
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.intent import router
from app.services.intent.router import (
    AGRONOMY,
    DEVICE_CONTROL,
    GARDEN_DATA,
    GREETING,
    PRODUCT_FEATURE,
    THANKS,
    LLMFewShotRouter,
    dinh_tuyen_fewshot,
)


def test_fewshot_examples_khong_rong():
    """Tap vi du few-shot phai co it nhat 30 vi du da dang cho 7 intent."""
    assert len(router.FEW_SHOT_EXAMPLES) >= 30
    intents = {ex["intent"] for ex in router.FEW_SHOT_EXAMPLES}
    assert AGRONOMY in intents
    assert GARDEN_DATA in intents
    assert DEVICE_CONTROL in intents
    assert PRODUCT_FEATURE in intents
    assert GREETING in intents
    assert THANKS in intents


def test_tao_prompt_fewshot_chua_du_thong_tin():
    """Prompt few-shot phai chua huong dan an toan, cac intent va cau hoi muc tieu."""
    r = LLMFewShotRouter()
    prompt = r.tao_prompt_fewshot("Cà chua có ưa bóng không?")
    assert "Intent Router" in prompt
    assert "QUY TẮC THIÊN LỆCH AN TOÀN" in prompt
    assert "Cà chua có ưa bóng không?" in prompt
    assert "JSON" in prompt


def test_rule_layer_uu_tien_truoc():
    """Khi Rule Layer da chac chan, Few-shot Router tra ve NGAY ket qua tu Rule.

    SUA 2026-08-28: ban dau khang dinh `do_tin_cay == 1.0`. Sai - va sai theo
    kieu chua bao gio chay: luat device_control tra 0.95 (router.py:364) tu
    truoc khi file test nay ra doi, nen phep khang dinh do khong the dung o
    bat ky thoi diem nao. Bo test do do lien tuc ke tu commit 8e5f93f.

    0.95 khong phai loi. Do la quy uoc cua tang rule: 1.0 danh cho cac mau
    khop nguyen van (chao hoi, cam on - dong 445/447/456), 0.95 cho mau ghep
    hai tin hieu (dong tu + thiet bi). Khang dinh mot con so cu the o day la
    buoc tang rule phai giu nguyen thang diem cho MOI luat, khong lien quan
    gi den dieu test nay canh.

    Dieu test nay canh la UU TIEN: rule thang thi khong goi LLM. Cong tac
    that nam o `phan_loai()` dong 621:

        if kq_rule.nguon != "mac_dinh" and kq_rule.do_tin_cay > 0.0:

    Nen khang dinh dung chinh hai dieu kien ay.
    """
    r = LLMFewShotRouter()
    # Cau ro rang la device_control
    kq = r.phan_loai("Bật máy bơm khu A giúp tôi")
    assert kq.nhan == DEVICE_CONTROL
    assert kq.nguon == "rule"
    assert kq.do_tin_cay > 0.0, "khong vuot duoc cong uu tien -> se roi xuong LLM"


def test_fewshot_heuristic_fallback_khi_chua_co_llm():
    """Khi khong co LLM client, heuristic gán do_tin_cay > 0.0 thay vi 0.0 mac dinh."""
    r = LLMFewShotRouter()
    # Cau hoi nong hoc khong trung rule cu the
    kq = r.phan_loai("Nhiệt độ thích hợp để quả cà chua chín đều là bao nhiêu độ C?")
    assert kq.nhan == AGRONOMY
    assert kq.do_tin_cay >= 0.80
    assert kq.nguon in ("few_shot_heuristic", "rule")


class _ClientGia:
    """Client gia theo DUNG giao uoc that (llm/base.py:81).

    SUA 2026-08-28: ban cu dung MagicMock voi `.goi()` tra ve object co
    `.van_ban`. Ca hai ten deu KHONG ton tai trong ma that - giao uoc la
    `sinh(prompt, *, json_mode, max_token_ra)` tra ve KetQuaLLM co `.text`.
    MagicMock nhan moi thuoc tinh nen no che mat sai lech do: test xanh trong
    khi dua client that vao se AttributeError ngay dong dau.

    Dung lop that thay vi MagicMock chinh la de mot sai lech nhu vay khong the
    lot qua lan nua.
    """

    def __init__(self, text: str):
        self._text = text
        self.so_lan_goi = 0
        self.prompt_cuoi = None

    def sinh(self, prompt, *, json_mode=False, max_token_ra=None):
        from app.services.llm.base import KetQuaLLM
        self.so_lan_goi += 1
        self.prompt_cuoi = prompt
        return KetQuaLLM(text=self._text, token_vao=0, token_ra=0,
                         token_suy_nghi=0, latency_ms=0,
                         model="gia", provider="test")


def test_fewshot_voi_mock_llm_client():
    """Kiem tra phan loai khi co LLM client tra ve JSON chuan."""
    client = _ClientGia(
        '{"intent": "garden_data", "confidence": 0.96, "reason": "user_asking_realtime_status"}')

    r = LLMFewShotRouter(llm_client=client)
    # Cau hoi bien ma rule tra ve mac_dinh (0.0)
    kq = r.phan_loai("Cho xem tình hình thực tế")
    assert kq.nhan == GARDEN_DATA
    assert kq.do_tin_cay == 0.96
    assert kq.nguon == "few_shot_llm"
    assert client.so_lan_goi == 1, "khong goi den model - nhanh LLM khong chay"


def test_fewshot_go_duoc_rao_ba_dau_backtick():
    """Model hay boc JSON trong ```json ... ```. Phai go dung tien to.

    Canh loi cu: `.strip("```json")` go theo TAP KY TU nen an mat chu that o
    hai dau. Cau tra loi bat dau bang "n" (vi du nhan `none`) se bi cat.
    """
    client = _ClientGia(
        '```json\n{"intent": "device_control", "confidence": 0.9, "reason": "n"}\n```')
    kq = LLMFewShotRouter(llm_client=client).phan_loai("Cho xem tình hình thực tế")
    assert kq.nhan == DEVICE_CONTROL
    assert kq.nguon == "few_shot_llm"


def test_fewshot_hong_thi_tut_xuong_heuristic_va_KEU():
    """Model hong -> khong duoc chan luong, nhung PHAI in canh bao.

    Im lang o day nghia la tang LLM chet ma he thong van bao cao nhu dang chay
    du hai tang - dung kieu suy giam im lang ma hybrid.py:70 co y tranh.
    """
    class _Hong:
        def sinh(self, prompt, *, json_mode=False, max_token_ra=None):
            raise RuntimeError("mang chet")

    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        kq = LLMFewShotRouter(llm_client=_Hong()).phan_loai(
            "Nhiệt độ thích hợp để quả cà chua chín đều là bao nhiêu độ C?")
    assert kq.nhan == AGRONOMY
    assert kq.nguon.startswith("few_shot_"), "phai tut xuong heuristic"
    assert "canh bao" in buf.getvalue().lower(), "hong ma khong keu"


def test_fewshot_tu_choi_nhan_la():
    """Model tra ve nhan khong nam trong 4+2 nhan -> khong duoc tin."""
    client = _ClientGia('{"intent": "xxx_khong_co_that", "confidence": 0.99}')
    import io
    import contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        kq = LLMFewShotRouter(llm_client=client).phan_loai("Cho xem tình hình thực tế")
    assert kq.nguon != "few_shot_llm", "nhan la ma van duoc dung"


def test_dinh_tuyen_fewshot_helper():
    """Ham dinh_tuyen_fewshot goi chay muot ma."""
    kq = dinh_tuyen_fewshot("Chào buổi sáng bot NextFarm")
    assert kq.nhan == GREETING
    assert kq.do_tin_cay > 0.0


# ---------------------------------------------------------------------------
# Cong INTENT_FEWSHOT: mac dinh TAT, va pipeline phai di qua cong nay.
# ---------------------------------------------------------------------------


def test_mac_dinh_tat_tang_fewshot(monkeypatch):
    """Khong dat INTENT_FEWSHOT thi duong song KHONG duoc goi LLM.

    Day la rao chan cho tinh toan ven cua so lieu: C0/C1/C2 do tren router
    thuan rule. Neu mot lan sua vo y bat tang LLM len mac dinh, moi con so
    trong bao cao lap tuc mo ta mot he thong khac voi he thong dang chay.
    """
    from app.services.intent import router as R

    monkeypatch.delenv("INTENT_FEWSHOT", raising=False)
    monkeypatch.setattr(R, "dung_fewshot", lambda: R._BAT and False)
    assert R.dinh_tuyen("Bật máy bơm khu A").nguon == "rule"


def test_co_bat_thi_moi_goi_llm(monkeypatch):
    """Bat co -> nhanh LLM duoc dung; khong bat -> khong."""
    from app.services.intent import router as R

    goi = []

    class _C:
        def sinh(self, prompt, *, json_mode=False, max_token_ra=None):
            from app.services.llm.base import KetQuaLLM
            goi.append(1)
            return KetQuaLLM(text='{"intent": "garden_data", "confidence": 0.9}',
                             token_vao=0, token_ra=0, token_suy_nghi=0,
                             latency_ms=0, model="gia", provider="test")

    monkeypatch.setattr(R, "dung_fewshot", lambda: True)
    monkeypatch.setattr("app.services.llm.tao_client", lambda *a, **k: _C())
    kq = R.dinh_tuyen("Cho xem tình hình thực tế")
    assert goi, "bat co roi ma khong goi model"
    assert kq.nhan == GARDEN_DATA


def test_pipeline_di_qua_dinh_tuyen_chu_khong_goi_thang_phan_loai():
    """Doc ma nguon: pipeline phai goi `dinh_tuyen`, khong goi thang `phan_loai`.

    Goi thang `phan_loai` la di vong qua cong INTENT_FEWSHOT - luc do bat co
    trong .env se khong co tac dung gi, va nguoi van hanh khong the biet.
    """
    src = (ROOT / "app" / "services" / "pipeline.py").read_text(encoding="utf-8")
    assert "dinh_tuyen(cau_hoi" in src, "pipeline khong di qua cong dinh tuyen"
    assert "phan_loai(cau_hoi" not in src, "pipeline goi thang phan_loai, vong qua cong"
