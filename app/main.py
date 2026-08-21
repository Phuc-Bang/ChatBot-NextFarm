"""
FastAPI - hai giao dien tach biet (muc 34).

    /            trang chat cho nong dan
    /admin       trang quan tri cho NextFarm xem he thong da chan gi

VI SAO TACH HAI TRANG

Trang admin hien TOAN BO cau hoi nguoi dung va log he thong. Gop chung vao
trang chat la de lo du lieu nguoi khac cho bat ky ai mo trang.

Chay LOCAL nen chua co dang nhap - da thong nhat voi nguoi dung. Neu ve sau
deploy ra ngoai thi BAT BUOC phai them khoa cho /admin va /api/admin/*.
Ghi o day de khong ai quen.

NAP MODEL LUC KHOI DONG
Nap model embedding mat ~16 giay (do duoc). Nap trong lifespan de nguoi dung
dau tien khong phai cho - neu de nap lan dau khi co request thi cau hoi dau
tien mat 16s trong khi ngan sach ASM-01 la 5s.
"""

from __future__ import annotations

# sentence_transformers PHAI nap truoc psycopg - xem eval_retrieval.py.
# Nap sai thu tu lam tien trinh segfault im lang (exit 139).
import sentence_transformers  # noqa: F401

import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.core.config import lay, nap_env

BASE = Path(__file__).resolve().parents[1]
WEB = BASE / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    nap_env()
    t = time.time()
    try:
        from app.services.retrieval.vector import _nap
        _nap()
        app.state.san_sang = True
        print("Da nap model embedding trong " + str(round(time.time() - t, 1))
              + "s")
    except Exception as e:                                 # noqa: BLE001
        # KHONG chet han: hai kenh tu khoa van chay duoc. Nhung phai bao ro
        # de khong ai tuong he thong dang chay du ba kenh.
        app.state.san_sang = False
        print("CANH BAO: khong nap duoc kenh vector - " + str(e)[:200])
        print("He thong van chay bang FTS + trigram, chat luong thap hon.")
    yield


app = FastAPI(title="ChatBot NextFarm - Bai toan A", lifespan=lifespan)


class CauHoiVao(BaseModel):
    cau_hoi: str = Field(min_length=1, max_length=2000)
    context_turns: list[str] = Field(default_factory=list, max_length=10)


@app.post("/api/chat")
def chat(v: CauHoiVao, nen: BackgroundTasks):
    from app.services.pipeline import tra_loi_cau_hoi

    r = tra_loi_cau_hoi(v.cau_hoi, v.context_turns or None)

    # Ghi log chay NEN, khong nam tren duong tra loi.
    #
    # Da va phai that: ghi_query_log() treo o psycopg.connect() lam MOI
    # request /api/chat khong bao gio tra ve, du cau tra loi da san sang tu
    # 0,01s. Cau "bat van 3 trong 10 phut" dang le ton 6ms va 0 token.
    # try/except cu khong cuu duoc vi TREO KHONG PHAI EXCEPTION.
    #
    # Hai lop bao ve, can ca hai:
    #   1. ket_noi() nay luon co connect_timeout (app/core/db.py)
    #   2. ghi log khong con chan cau tra loi (dong duoi)
    nen.add_task(_ghi_log_an_toan, r)

    return {
        "tra_loi": r.tra_loi,
        "da_tu_choi": r.da_tu_choi,
        "ly_do_tu_choi": r.ly_do_tu_choi,
        "intent": r.intent,
        "cay": r.cay,
        "nguon": [{
            "chunk_id": n.chunk_id,
            "tieu_de": n.document_title,
            "co_quan": n.publisher,
            "url": n.url,
            "trich": " ".join(n.text.split())[:400],
            "tier": n.source_tier,
        } for n in r.nguon],
        "latency_ms": r.latency_ms,
        "tong_latency_ms": r.tong_latency_ms,
    }


def _ghi_log_an_toan(r) -> None:
    """Ghi query_log, nuot moi loi. Chay nen nen khong ai doi ket qua."""
    from app.core.nhat_ky import ghi_query_log
    try:
        ghi_query_log(r)
    except Exception as e:                                 # noqa: BLE001
        # Im lang o day la mat du lieu chan bia - phai in ra.
        print("khong ghi duoc query_log: " + str(e)[:150])


@app.get("/api/health")
def health():
    return {"trang_thai": "ok", "model": lay("LLM_MODEL"),
            "embedding": lay("EMBEDDING_MODEL"),
            "kenh_vector": bool(getattr(app.state, "san_sang", False))}


# ---------------------------------------------------------------------------
# API cho trang admin
# ---------------------------------------------------------------------------

@app.get("/api/admin/tong_quan")
def admin_tong_quan():
    from app.core.nhat_ky import tong_quan
    return tong_quan()


@app.get("/api/admin/nhat_ky")
def admin_nhat_ky(limit: int = 50, chi_tu_choi: bool = False):
    from app.core.nhat_ky import doc_nhat_ky
    return doc_nhat_ky(limit=min(limit, 500), chi_tu_choi=chi_tu_choi)


@app.get("/api/admin/kho_tri_thuc")
def admin_kho():
    from app.core.nhat_ky import thong_ke_kho
    return thong_ke_kho()


# ---------------------------------------------------------------------------
# Trang tinh
# ---------------------------------------------------------------------------

if (WEB / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=WEB / "assets"), name="assets")


@app.get("/")
def trang_chat():
    f = WEB / "chat.html"
    if not f.exists():
        return JSONResponse({"loi": "chua co frontend/chat.html"}, 404)
    return FileResponse(f)


@app.get("/admin")
def trang_admin():
    f = WEB / "admin.html"
    if not f.exists():
        return JSONResponse({"loi": "chua co frontend/admin.html"}, 404)
    return FileResponse(f)


@app.get("/report")
def trang_report():
    f = WEB / "report.html"
    if not f.exists():
        return JSONResponse({"loi": "chua co frontend/report.html"}, 404)
    return FileResponse(f)
