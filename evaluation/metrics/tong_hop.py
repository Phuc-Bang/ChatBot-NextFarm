"""
Tong hop chi so tu ket qua cham tung case — muc 30.5.

DEC-025: MOI CHI SO BAO CAO THEO CAP

`answer_rate` va `accuracy_when_answered` phai di cung nhau. Tach ra thi mot
he thong tu choi tat ca se dat 0% bia dat va trong nhu hoan hao - trong khi
no vo dung. Ham `bang()` o day khong cho phep in mot ve.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field


@dataclass
class ChiSo:
    tong_case: int = 0

    # Cap bat buoc (DEC-025)
    so_tra_loi: int = 0
    so_tra_loi_dung: int = 0
    so_tra_loi_chua_cham: int = 0

    # Tu choi
    so_phai_tu_choi: int = 0
    so_tu_choi_dung: int = 0
    so_tu_choi_oan: int = 0

    # Nhom chong bia - muc tieu deu bang 0
    fabricated_garden_data: int = 0
    fabricated_feature: int = 0
    device_control_leak: int = 0
    out_of_scope_leak: int = 0
    numeric_hallucination: int = 0

    # Hieu nang / chi phi
    token_vao: int = 0
    token_ra: int = 0
    latency: list[int] = field(default_factory=list)
    so_loi_goi: int = 0

    theo_nhom: Counter = field(default_factory=Counter)
    theo_nhom_dung: Counter = field(default_factory=Counter)

    # ------------------------------------------------------------------
    @property
    def answer_rate(self) -> float:
        return self.so_tra_loi / self.tong_case if self.tong_case else 0.0

    @property
    def accuracy_when_answered(self) -> float | None:
        """None khi khong co case nao cham duoc tu dong.

        Tra ve 0.0 trong truong hop do se la noi doi: 0% chinh xac va
        "khong do duoc" la hai chuyen hoan toan khac nhau.
        """
        n = self.so_tra_loi_dung + self.so_sai_da_cham
        return self.so_tra_loi_dung / n if n else None

    @property
    def so_sai_da_cham(self) -> int:
        return (self.so_tra_loi - self.so_tra_loi_dung
                - self.so_tra_loi_chua_cham)

    @property
    def false_answer_rate(self) -> float:
        return self.so_sai_da_cham / self.tong_case if self.tong_case else 0.0

    @property
    def over_abstention_rate(self) -> float:
        return self.so_tu_choi_oan / self.tong_case if self.tong_case else 0.0

    @property
    def abstention_recall(self) -> float | None:
        if not self.so_phai_tu_choi:
            return None
        return self.so_tu_choi_dung / self.so_phai_tu_choi

    @property
    def tong_bia(self) -> int:
        return (self.fabricated_garden_data + self.fabricated_feature
                + self.device_control_leak + self.out_of_scope_leak
                + self.numeric_hallucination)

    def p(self, q: float) -> int:
        if not self.latency:
            return 0
        s = sorted(self.latency)
        i = min(int(q * len(s)), len(s) - 1)
        return s[i]


def _pc(x: float) -> str:
    return format(x * 100, ".1f") + "%"


def bang(c: ChiSo, ten: str, model: str, phien_ban: str,
         chi_phi_usd: float | None = None) -> str:
    """Bang so theo mau muc 30.2.

    Luon in ca answer_rate lan accuracy_when_answered (DEC-025).
    """
    d = []
    a = d.append
    a("=" * 72)
    a("CAU HINH " + ten + "  |  model " + model + "  |  tap kiem thu "
      + phien_ban)
    a("=" * 72)
    a("Tong case                    : " + str(c.tong_case))
    if c.so_loi_goi:
        a("Loi goi model                : " + str(c.so_loi_goi)
          + "   <- KHONG tinh la tra loi dung/sai")
    a("")
    a("--- Cap bat buoc (DEC-025) ---")
    a("answer_rate                  : " + _pc(c.answer_rate)
      + "   (" + str(c.so_tra_loi) + "/" + str(c.tong_case) + ")")
    acc = c.accuracy_when_answered
    if acc is None:
        a("accuracy_when_answered       : khong do duoc "
          "(khong case nao cham tu dong duoc)")
    else:
        a("accuracy_when_answered       : " + _pc(acc)
          + "   (" + str(c.so_tra_loi_dung) + "/"
          + str(c.so_tra_loi_dung + c.so_sai_da_cham) + " case cham duoc)")
    if c.so_tra_loi_chua_cham:
        a("  chua cham tu dong          : " + str(c.so_tra_loi_chua_cham)
          + "   (cau mo, khong co dap an chuan)")
    a("false_answer_rate            : " + _pc(c.false_answer_rate))
    a("over_abstention_rate         : " + _pc(c.over_abstention_rate)
      + "   (" + str(c.so_tu_choi_oan) + " case tu choi oan)")
    ar = c.abstention_recall
    if ar is not None:
        a("abstention_recall            : " + _pc(ar)
          + "   (" + str(c.so_tu_choi_dung) + "/"
          + str(c.so_phai_tu_choi) + ")")
    a("")
    a("--- Chong bia (muc tieu: TAT CA bang 0) ---")
    for ten_cs, v in (
            ("fabricated_garden_data", c.fabricated_garden_data),
            ("fabricated_feature", c.fabricated_feature),
            ("device_control_leak", c.device_control_leak),
            ("out_of_scope_leak", c.out_of_scope_leak),
            ("numeric_hallucination", c.numeric_hallucination)):
        a("  " + ten_cs.ljust(27) + ": " + str(v)
          + ("" if v == 0 else "   <-- CHUA DAT"))
    a("  " + "TONG".ljust(27) + ": " + str(c.tong_bia))
    a("")
    a("--- Hieu nang / chi phi ---")
    a("latency p50 / p95            : " + str(c.p(0.50)) + "ms / "
      + str(c.p(0.95)) + "ms")
    n = max(c.tong_case - c.so_loi_goi, 1)
    a("token trung binh moi luot    : vao " + str(round(c.token_vao / n))
      + "  ra " + str(round(c.token_ra / n))
      + "   <- Ti va To cua muc 37.5")
    if chi_phi_usd is not None:
        a("chi phi ca luot chay         : $" + format(chi_phi_usd, ".4f"))
    a("")
    a("--- Theo nhom ---")
    for g in sorted(c.theo_nhom):
        a("  " + g.ljust(24) + str(c.theo_nhom_dung[g]) + "/"
          + str(c.theo_nhom[g]))
    return "\n".join(d)
