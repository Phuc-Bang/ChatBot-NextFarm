"""
Ghi va doc `query_log` (muc 20, 21.2, 38).

BANG NAY DA CO TU P5 - KHONG TAO BANG MOI

`query_log` da co san `latency_ms JSONB`, `token_in`, `token_out` voi ghi
chu "Ghi tu P7 chu khong doi den luc can bao cao moi them". Tao mot bang
`llm_usage_log` song song se sinh ra HAI NGUON SU THAT cho cung mot con so,
va khi hai bang lech nhau thi khong biet tin bang nao.

`latency_ms` la JSONB co chu dich: muc 21.2 doi do TUNG CHANG chu khong phai
mot con so tong. Ly do o muc 21.3 - vuot ngan sach thi phai biet CAT CHANG
NAO, ma mot con so tong khong noi duoc dieu do.

KHONG GHI THONG TIN DINH DANH (muc 38.2)
Chi ghi cau hoi va ket qua xu ly. Khong user_id, khong IP, khong session
gan voi nguoi that.
"""

from __future__ import annotations

from typing import Any

from app.core.db import ket_noi


class LoiDocNhatKy(Exception):
    """Khong doc duoc du lieu nhat ky.

    Ton tai de tang tren PHAN BIET duoc "khong co du lieu" voi "khong doc
    duoc du lieu". Truoc day ca hai deu tra ve gia tri binh thuong, nen mot
    su co CSDL hien ra y het mot he thong chua ai dung - hoac te hon, hien ra
    mot bo so day du trong nhu that.
    """


def ghi_query_log(kq) -> None:
    """Ghi mot luot hoi. `kq` la KetQuaHoi cua pipeline."""
    import json

    with ket_noi() as con, con.cursor() as cur:
        cur.execute(
            "INSERT INTO query_log ("
            "  question_raw, intent, intent_confidence, crop,"
            "  retrieved_chunk_ids, final_answer, abstained, abstain_reason,"
            "  latency_ms, token_in, token_out"
            ") VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (kq.cau_hoi, kq.intent, kq.intent_do_tin_cay,
             (kq.cay or [None])[0],
             [n.chunk_id for n in kq.nguon],
             kq.tra_loi, kq.da_tu_choi, kq.ly_do_tu_choi,
             json.dumps(kq.latency_ms), kq.token_vao, kq.token_ra))
        con.commit()


def doc_nhat_ky(limit: int = 50, chi_tu_choi: bool = False) -> list[dict]:
    """Doc log gan nhat."""
    dk = " WHERE abstained" if chi_tu_choi else ""
    try:
        with ket_noi() as con, con.cursor() as cur:
            cur.execute(
                "SELECT query_id, ts, question_raw, intent, crop, final_answer,"
                "       abstained, abstain_reason, latency_ms, token_in, token_out,"
                "       retrieved_chunk_ids "
                "FROM query_log" + dk + " ORDER BY ts DESC LIMIT %s", (limit,))
            ra = []
            for r in cur.fetchall():
                ra.append({
                    "id": r[0], "thoi_diem": r[1].isoformat() if r[1] else None,
                    "cau_hoi": r[2], "intent": r[3], "cay": r[4],
                    "tra_loi": r[5], "da_tu_choi": r[6], "ly_do": r[7],
                    "latency_ms": r[8], "token_vao": r[9], "token_ra": r[10],
                    "so_nguon": len(r[11] or []),
                })
            return ra
    except Exception as e:
        raise LoiDocNhatKy("khong doc duoc query_log: " + str(e)[:200]) from e


def tong_quan() -> dict[str, Any]:
    """So lieu tong hop cho trang admin."""
    from app.core.config import lay
    from app.services.llm.gia import NGAY_TRA_CUU, chi_phi_usd

    model = lay("LLM_MODEL") or ""
    try:
        with ket_noi() as con, con.cursor() as cur:
            cur.execute(
                "SELECT count(*), count(*) FILTER (WHERE abstained),"
                "       coalesce(sum(token_in),0), coalesce(sum(token_out),0) "
                "FROM query_log")
            tong, tu_choi, t_vao, t_ra = cur.fetchone()

            cur.execute(
                "SELECT abstain_reason, count(*) FROM query_log "
                "WHERE abstained AND abstain_reason IS NOT NULL "
                "GROUP BY 1 ORDER BY 2 DESC")
            theo_ly_do = [{"ly_do": r[0], "so_luot": r[1]} for r in cur.fetchall()]

            cur.execute(
                "SELECT intent, count(*) FROM query_log "
                "WHERE intent IS NOT NULL GROUP BY 1 ORDER BY 2 DESC")
            theo_intent = [{"intent": r[0], "so_luot": r[1]}
                           for r in cur.fetchall()]

            cur.execute(
                "SELECT percentile_disc(0.5) WITHIN GROUP (ORDER BY t),"
                "       percentile_disc(0.95) WITHIN GROUP (ORDER BY t) FROM ("
                "  SELECT (SELECT sum(value::int) FROM jsonb_each_text(latency_ms))"
                "  AS t FROM query_log WHERE latency_ms IS NOT NULL) s")
            p = cur.fetchone()

            cur.execute(
                "SELECT key, round(avg(value::int)) FROM query_log,"
                "  jsonb_each_text(latency_ms) WHERE latency_ms IS NOT NULL"
                "  GROUP BY 1 ORDER BY 2 DESC")
            theo_chang = [{"chang": r[0], "trung_binh_ms": int(r[1])}
                          for r in cur.fetchall()]

        try:
            tien = chi_phi_usd(model, int(t_vao), int(t_ra))
        except Exception:
            tien = None

        n = max(tong, 1)
        return {
            "tong_luot": tong,
            "so_tu_choi": tu_choi,
            "ty_le_tu_choi": round(tu_choi / n * 100, 1),
            "token_vao": int(t_vao), "token_ra": int(t_ra),
            "Ti_trung_binh": round(int(t_vao) / n),
            "To_trung_binh": round(int(t_ra) / n),
            "chi_phi_usd": tien,
            "model": model,
            "ngay_tra_gia": NGAY_TRA_CUU,
            # None chu KHONG phai 11/8084. "Chua do duoc" va "do duoc 11ms"
            # la hai chuyen khac nhau - dien so vao cho chua do la bia.
            "latency_p50_ms": p[0] if p else None,
            "latency_p95_ms": p[1] if p else None,
            "theo_ly_do": theo_ly_do,
            "theo_intent": theo_intent,
            "theo_chang": theo_chang,
        }
    except Exception as e:
        raise LoiDocNhatKy("khong tong hop duoc nhat ky: " + str(e)[:200]) from e


def thong_ke_kho() -> dict[str, Any]:
    """So lieu kho tri thuc."""
    try:
        with ket_noi() as con, con.cursor() as cur:
            cur.execute("SELECT count(*), count(*) FILTER (WHERE approved) "
                        "FROM document")
            tl_tong, tl_duyet = cur.fetchone()
            cur.execute("SELECT count(*), count(*) FILTER (WHERE is_high_risk) "
                        "FROM chunk")
            c_tong, c_rui_ro = cur.fetchone()
            cur.execute("SELECT count(*) FROM indexable_chunk")
            c_idx = cur.fetchone()[0]
            cur.execute("SELECT count(*), count(*) FILTER (WHERE verified) "
                        "FROM fact")
            f_tong, f_duyet = cur.fetchone()
            cur.execute("SELECT crop, count(*) FROM indexable_chunk "
                        "WHERE crop IS NOT NULL GROUP BY 1 ORDER BY 2 DESC")
            theo_cay = [{"cay": r[0], "so_chunk": r[1]} for r in cur.fetchall()]

        return {
            "tai_lieu_tong": tl_tong, "tai_lieu_da_duyet": tl_duyet,
            "chunk_tong": c_tong, "chunk_index_duoc": c_idx,
            "chunk_rui_ro_cao": c_rui_ro,
            "chunk_bi_chan": c_tong - c_idx,
            "fact_tong": f_tong, "fact_da_duyet": f_duyet,
            "theo_cay": theo_cay,
        }
    except Exception as e:
        raise LoiDocNhatKy("khong doc duoc thong ke kho: " + str(e)[:200]) from e
