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


def test_fewshot_voi_mock_llm_client():
    """Kiem tra phan loai khi co LLM client tra ve JSON chuan."""
    mock_client = MagicMock()
    mock_res = MagicMock()
    mock_res.van_ban = '{"intent": "garden_data", "confidence": 0.96, "reason": "user_asking_realtime_status"}'
    mock_client.goi.return_value = mock_res

    r = LLMFewShotRouter(llm_client=mock_client)
    # Cau hoi bien ma rule tra ve mac_dinh (0.0)
    kq = r.phan_loai("Cho xem tình hình thực tế")
    assert kq.nhan == GARDEN_DATA
    assert kq.do_tin_cay == 0.96
    assert kq.nguon == "few_shot_llm"


def test_dinh_tuyen_fewshot_helper():
    """Ham dinh_tuyen_fewshot goi chay muot ma."""
    kq = dinh_tuyen_fewshot("Chào buổi sáng bot NextFarm")
    assert kq.nhan == GREETING
    assert kq.do_tin_cay > 0.0
