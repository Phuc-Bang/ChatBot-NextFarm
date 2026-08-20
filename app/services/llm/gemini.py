"""
Client Gemini — cai dat LLMClient (muc 17).

BA DIEU DO DUOC TREN KEY THAT, KHONG PHAI DOC TAI LIEU

1. TEN TRUONG TOKEN
   SDK google-genai 2.19.0 tra ve `response.usage_metadata` voi
   `prompt_token_count` / `candidates_token_count` / `thoughts_token_count`.
   Tai lieu quickstart hien tai mo ta mot API khac (`interactions.create`,
   `usage.total_input_tokens`) - ban do KHONG dung voi SDK nay. Da xac nhan
   bang cach in nguyen object ra roi moi viet parser.

2. THINKING TOKEN LA HOA DON AN
   Gemini 2.5 mac dinh bat che do suy nghi. Do that:

       cau hoi hai chu, mac dinh    : ra=3    think=1848  tong=1865
       cung cau hoi, budget=0       : ra=5    think=0     tong=19

   Thinking token duoc tinh tien NHU token dau ra. Bo qua no thi uoc luong
   chi phi muc 37.5 sai hang chuc lan. Te hon: so nay khong on dinh giua cac
   lan goi (do duoc 1848 roi 135 cho cung mot cau) nen khong the uoc luong.

   PoC tat han (`thinking_budget=0`). Ly do khong chi la tien:
     - latency 1.9s -> 0.9s, dung vao ngan sach ASM-01
     - viec cua LLM o day la doc Evidence Pack roi viet lai co trich dan,
       khong phai suy luan. Can suy luan moi khong bia thi KIEN TRUC sai -
       Grounding Validator moi la thu chan bia (muc 18)
     - do duoc: ban budget=0 tra loi tieng Viet CO DAU dung hon ban mac dinh

3. FREE TIER SE DUNG TRAN
   Chay 222 case lien tuc chac chan gap 429. Client tu lui va thu lai; noi
   goi phai luu ket qua sau TUNG case (xem runner) de mat 1 case chu khong
   mat ca luot do.
"""

from __future__ import annotations

import os
import random
import time

from app.services.llm.base import KetQuaLLM

# Ma loi dang thu lai. 429 = het quota/nhip; 500/503 = loi phia Google.
# KHONG thu lai 400/403: sai key hay sai tham so thi thu lai bao nhieu lan
# cung the, chi lam cham va che mat loi that.
MA_THU_LAI = (429, 500, 502, 503, 504)

SO_LAN_THU = 5
CHO_DAU_GIAY = 2.0


class GeminiClient:
    """Goi Gemini, luon tra ve so token do duoc."""

    ten_provider = "gemini"

    def __init__(self, model: str | None = None, api_key: str | None = None,
                 thinking_budget: int = 0, timeout_giay: int = 120):
        self.ten_model = model or os.environ.get("LLM_MODEL", "gemini-2.5-flash")
        self.thinking_budget = thinking_budget
        # Bat len khi model tra ve 400 vi khong nhan thinking_config.
        self._bo_thinking = False
        self.timeout_giay = timeout_giay

        key = api_key or os.environ.get("GEMINI_API_KEY") or \
            os.environ.get("LLM_API_KEY")
        if not key:
            raise RuntimeError(
                "Thieu GEMINI_API_KEY. Dien vao .env (.env da nam trong "
                ".gitignore nen khong len GitHub).")

        from google import genai
        self._genai = genai
        self._client = genai.Client(api_key=key)

    # ------------------------------------------------------------------
    def _config(self, json_mode: bool, max_token_ra: int | None,
                bo_thinking: bool = False):
        """Cau hinh mot lan goi.

        `bo_thinking` bo han truong thinking_config. Can co vi KHONG PHAI
        model nao cung nhan thinking_budget=0 - do tren key that:

            gemini-2.5-flash        thinking_budget=0  -> OK
            gemini-3.6-flash        thinking_budget=0  -> 400 INVALID_ARGUMENT
            gemini-3.5-flash-lite   thinking_budget=0  -> 400 INVALID_ARGUMENT

        Ho 3.x moi khong cho tat suy nghi bang cach nay. Gap 400 thi tu bo
        truong do va goi lai (xem sinh()), thay vi coi nhu that bai - vi
        nguyen nhan la KHONG TUONG THICH THAM SO chu khong phai loi noi dung.
        """
        from google.genai import types
        kw = {}
        if not bo_thinking:
            # thinking_budget=0 phai truyen TUONG MINH. Bo trong la Gemini tu
            # quyet dinh, va no se bat suy nghi.
            kw["thinking_config"] = types.ThinkingConfig(
                thinking_budget=self.thinking_budget)
        if json_mode:
            kw["response_mime_type"] = "application/json"
        if max_token_ra:
            kw["max_output_tokens"] = max_token_ra
        return types.GenerateContentConfig(**kw)

    @staticmethod
    def _ma_loi(e: Exception) -> int | None:
        for tt in ("code", "status_code"):
            v = getattr(e, tt, None)
            if isinstance(v, int):
                return v
        s = str(e)
        for ma in MA_THU_LAI:
            if str(ma) in s:
                return ma
        return None

    # ------------------------------------------------------------------
    def sinh(self, prompt: str, *, json_mode: bool = False,
             max_token_ra: int | None = None) -> KetQuaLLM:
        cfg = self._config(json_mode, max_token_ra, self._bo_thinking)
        loi_cuoi = ""

        for lan in range(SO_LAN_THU):
            t0 = time.time()
            try:
                r = self._client.models.generate_content(
                    model=self.ten_model, contents=prompt, config=cfg)
            except Exception as e:                        # noqa: BLE001
                ma = self._ma_loi(e)
                loi_cuoi = type(e).__name__ + ": " + str(e)[:300]

                # 400 khi dang dat thinking_config -> thu lai MOT lan khong co
                # truong do.
                #
                # Khong loc theo chu "thinking" trong thong bao: Google tra ve
                # dung mot cau "Request contains an invalid argument." khong
                # noi truong nao sai. Doi chieu theo chu se khong bao gio khop.
                #
                # Chi thu DUNG MOT LAN va nho ket qua, nen neu 400 den tu
                # nguyen nhan khac thi lan goi lai cung 400 va loi that duoc
                # bao cao binh thuong - khong che giau duoc gi.
                if "400" in str(e) and not self._bo_thinking:
                    self._bo_thinking = True
                    cfg = self._config(json_mode, max_token_ra, True)
                    print("  (model nay khong nhan thinking_budget - da bo)")
                    continue

                if ma in MA_THU_LAI and lan < SO_LAN_THU - 1:
                    # Lui theo cap so nhan + nhieu ngau nhien, tranh nhieu
                    # tien trinh cung dap lai mot luc.
                    cho = CHO_DAU_GIAY * (2 ** lan) + random.uniform(0, 1)
                    print("  [" + str(ma) + "] cho " + str(round(cho, 1))
                          + "s roi thu lai (" + str(lan + 1) + "/"
                          + str(SO_LAN_THU) + ")")
                    time.sleep(cho)
                    continue
                return KetQuaLLM(
                    text="", token_vao=0, token_ra=0, token_suy_nghi=0,
                    latency_ms=int((time.time() - t0) * 1000),
                    model=self.ten_model, provider=self.ten_provider,
                    loi=loi_cuoi)

            dt = int((time.time() - t0) * 1000)
            u = getattr(r, "usage_metadata", None)

            def lay(ten: str) -> int:
                return int(getattr(u, ten, None) or 0) if u else 0

            fr = None
            try:
                if r.candidates:
                    fr = str(r.candidates[0].finish_reason)
            except Exception:                              # noqa: BLE001
                pass

            # r.text co the la None khi bi chan boi bo loc an toan. Ep ve
            # chuoi rong nhung GIU finish_reason de tang tren biet vi sao.
            return KetQuaLLM(
                text=(r.text or "").strip(),
                token_vao=lay("prompt_token_count"),
                token_ra=lay("candidates_token_count"),
                token_suy_nghi=lay("thoughts_token_count"),
                latency_ms=dt, model=self.ten_model,
                provider=self.ten_provider, finish_reason=fr,
                raw_usage={
                    "prompt_token_count": lay("prompt_token_count"),
                    "candidates_token_count": lay("candidates_token_count"),
                    "thoughts_token_count": lay("thoughts_token_count"),
                    "total_token_count": lay("total_token_count"),
                })

        return KetQuaLLM(
            text="", token_vao=0, token_ra=0, token_suy_nghi=0, latency_ms=0,
            model=self.ten_model, provider=self.ten_provider,
            loi="het " + str(SO_LAN_THU) + " lan thu. " + loi_cuoi)
