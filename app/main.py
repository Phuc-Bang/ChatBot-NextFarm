"""
FastAPI - hai giao dien tach biet (muc 34).

    /            trang chat cho nong dan
    /admin       trang quan tri cho NextFarm xem he thong da chan gi

VI SAO TACH HAI TRANG

Trang admin hien TOAN BO cau hoi nguoi dung va log he thong. Gop chung vao
trang chat la de lo du lieu nguoi khac cho bat ky ai mo trang.

CANH CUA /admin (xem `kiem_quyen_admin`)

Truoc day chi co mot dong ghi chu "deploy ra ngoai thi nho them khoa". Ghi chu
khong chan duoc gi: doi `--host 127.0.0.1` thanh `0.0.0.0` la toan bo nhat ky
truy van - cau hoi nguyen van cua nguoi dung - mo ra internet, khong mot buoc
nao bat phai dung lai.

Nen bay gio co mot canh cua that, MAC DINH AN TOAN:

  - ADMIN_TOKEN co dat  -> moi request phai kem dung token do
  - ADMIN_TOKEN de trong -> chi chap nhan request tu chinh may dang chay
                            (loopback). Tu dia chi khac: 403 kem huong dan.

De trong van la trai nghiem PoC hom nay - `make serve` chay 127.0.0.1 nen
khong ai phai cau hinh gi. Cai doi la mot deploy quen cau hinh gio TU CHOI
thay vi lang le phuc vu.

KHONG chot co che xac thuc thay NextFarm. Token tinh la lop toi thieu de mac
dinh an toan; NextFarm van dat OAuth/SSO o reverse proxy duoc, luc do dat
ADMIN_TOKEN cho tang trong.

NAP MODEL LUC KHOI DONG
Nap model embedding mat ~16 giay (do duoc). Nap trong lifespan de nguoi dung
dau tien khong phai cho - neu de nap lan dau khi co request thi cau hoi dau
tien mat 16s trong khi ngan sach ASM-01 la 5s.
"""

from __future__ import annotations

try:
    import sentence_transformers  # noqa: F401
except ImportError:
    pass

import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, Request
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
# Canh cua /admin
# ---------------------------------------------------------------------------

# Dia chi duoc coi la "chinh may nay". ::1 va ::ffff:127.0.0.1 la dang IPv6
# cua cung mot thu - thieu chung thi trinh duyet mo localhost tren mot so may
# Windows se bi tu choi oan.
LOOPBACK = {"127.0.0.1", "::1", "::ffff:127.0.0.1", "localhost"}


def kiem_quyen_admin(req: Request):
    """Tra ve None neu duoc phep, hoac JSONResponse loi neu khong.

    Dung ham thuong chu khong dung Depends() de moi endpoint tu quyet dinh -
    trang /admin can tra HTML loi de doc duoc trong trinh duyet, con
    /api/admin/* tra JSON.
    """
    import hmac

    token = (lay("ADMIN_TOKEN") or "").strip()
    if token:
        # compare_digest chu khong phai == : so sanh chuoi thuong dung som o
        # ky tu dau khac nhau, do lech thoi gian do ro duoc tung ky tu.
        gui = (req.headers.get("X-Admin-Token")
               or req.query_params.get("token") or "")
        if hmac.compare_digest(gui, token):
            return None
        return JSONResponse({"loi": "sai hoac thieu ADMIN_TOKEN"}, 401)

    # Khong dat token -> chi phuc vu chinh may nay.
    # req.client co the None (test client, mot so ASGI server). Coi nhu
    # khong xac dinh duoc dia chi, va khong xac dinh duoc thi KHONG mo.
    dia_chi = req.client.host if req.client else None
    if dia_chi in LOOPBACK:
        return None
    return JSONResponse(
        {"loi": "/admin chi phuc vu may cuc bo khi chua dat ADMIN_TOKEN. "
                "Dat ADMIN_TOKEN trong .env roi goi lai kem header "
                "X-Admin-Token.",
         "dia_chi_goi": dia_chi}, 403)


# ---------------------------------------------------------------------------
# API cho trang admin
# ---------------------------------------------------------------------------

# 503 chu khong phai 200 kem du lieu mac dinh. Trang admin la cho trinh bay
# bang chung "he thong nay khong bia" - no khong duoc phep bia so cua chinh
# no. Doc khong duoc thi phai noi la doc khong duoc.

@app.get("/api/admin/tong_quan")
def admin_tong_quan(req: Request):
    if (chan := kiem_quyen_admin(req)) is not None:
        return chan
    from app.core.nhat_ky import LoiDocNhatKy, tong_quan
    try:
        return tong_quan()
    except LoiDocNhatKy as e:
        return JSONResponse({"loi": str(e)}, 503)


@app.get("/api/admin/nhat_ky")
def admin_nhat_ky(req: Request, limit: int = 50, chi_tu_choi: bool = False):
    if (chan := kiem_quyen_admin(req)) is not None:
        return chan
    from app.core.nhat_ky import LoiDocNhatKy, doc_nhat_ky
    try:
        return doc_nhat_ky(limit=min(limit, 500), chi_tu_choi=chi_tu_choi)
    except LoiDocNhatKy as e:
        return JSONResponse({"loi": str(e)}, 503)


@app.get("/api/admin/kho_tri_thuc")
def admin_kho(req: Request):
    if (chan := kiem_quyen_admin(req)) is not None:
        return chan
    from app.core.nhat_ky import LoiDocNhatKy, thong_ke_kho
    try:
        return thong_ke_kho()
    except LoiDocNhatKy as e:
        return JSONResponse({"loi": str(e)}, 503)


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
def trang_admin(req: Request):
    if (chan := kiem_quyen_admin(req)) is not None:
        return chan
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


@app.get("/expert")
@app.get("/phieu-cham")
def trang_expert():
    f = WEB / "expert.html"
    if not f.exists():
        return JSONResponse({"loi": "chua co frontend/expert.html"}, 404)
    return FileResponse(f)


@app.get("/api/expert/cases")
def lay_cases_chuyen_gia():
    try:
        from app.services.evaluation.expert_parser import doc_phieu_cham
        return {"cases": doc_phieu_cham(), "tong_so": len(doc_phieu_cham())}
    except Exception as e:
        return JSONResponse({"loi": str(e)}, 500)


@app.get("/api/expert/scores")
def lay_diem_chuyen_gia():
    score_file = BASE / "evaluation" / "results" / "expert_scores.json"
    if score_file.exists():
        import json
        try:
            return json.loads(score_file.read_text(encoding="utf-8"))
        except Exception:
            return {"scores": {}, "reviewer": "", "updated_at": ""}
    return {"scores": {}, "reviewer": "", "updated_at": ""}


@app.post("/api/expert/save")
async def luu_diem_chuyen_gia(req: Request):
    # Cung canh cua voi /admin. Endpoint nay GHI DE ban ghi danh gia chuyen
    # gia - thu duy nhat cho ra ty le chinh xac that cua he thong. De no mo
    # nghia la bat ky ai goi toi cung sua duoc ket qua nghiem thu.
    if (chan := kiem_quyen_admin(req)) is not None:
        return chan
    try:
        import json
        payload = await req.json()

        # Kiem truoc khi ghi de. Endpoint nay THAY THE toan bo ban ghi danh
        # gia - mot POST rong se xoa sach cong cham cua chuyen gia ma khong
        # bao gi. Da xay ra khi kiem thu: `curl -d '{}'` lam file con dung
        # hai ky tu.
        if not isinstance(payload, dict):
            return JSONResponse({"loi": "than yeu cau phai la object JSON"}, 400)
        nguoi = str(payload.get("reviewer") or "").strip()
        diem = payload.get("scores")
        if not nguoi:
            return JSONResponse(
                {"loi": "thieu 'reviewer' - diem cham phai kem ten nguoi "
                        "chiu trach nhiem"}, 400)
        if not isinstance(diem, dict) or not diem:
            return JSONResponse(
                {"loi": "thieu 'scores' - khong ghi de ban ghi danh gia bang "
                        "mot phieu rong"}, 400)

        score_file = BASE / "evaluation" / "results" / "expert_scores.json"
        score_file.parent.mkdir(parents=True, exist_ok=True)
        score_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"trang_thai": "ok", "message": "Da luu ket qua danh gia chuyen gia thanh cong"}
    except Exception as e:
        return JSONResponse({"loi": str(e)}, 500)

