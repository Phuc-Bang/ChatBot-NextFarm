"""
Embedding chay local bang sentence-transformers.

TIEN TO LA CHO DE SAI NHAT

Ho model E5 (va halong_embedding, vi no finetune tu multilingual-e5-base)
duoc huan luyen voi hai tien to khac nhau:

    "query: "   cho cau hoi
    "passage: " cho doan van trong kho

Dung sai - hoac bo han - thi model VAN CHAY, VAN tra ve vector, khong bao
loi gi ca. Chi co Recall tut xuong lang le. Day dung la kieu loi ma quy
chuan v2.0 canh bao nhieu lan: that bai phai la that bai, khong duoc lang le.

bge-m3 thi NGUOC LAI: no khong dung tien to. Them tien to vao bge-m3 la tu
lam ban dau vao.

Vi vay bang TIEN_TO o duoi la mot phan cua dinh nghia model, khong phai
tham so tuy chinh.
"""

from __future__ import annotations

import numpy as np

# ten ngan -> (duong dan HuggingFace, tien to cau hoi, tien to doan van)
#
# Chi ghi model DA KIEM la ton tai. Khong doan ten model.
MODEL = {
    # 278M, finetune tu multilingual-e5-base. VN-MTEB: 61,60 (hang dau nhom
    # cung co). Toi da 512 token.
    "halong": ("contextboxai/halong_embedding", "query: ", "passage: "),

    # 118M - nho nhat, nhanh nhat. VN-MTEB: 60,66 (chi kem halong 0,94 diem
    # trong khi nho hon 2,4 lan). Ung vien that su chu khong phai de so sanh.
    "e5-small": ("intfloat/multilingual-e5-small", "query: ", "passage: "),

    # 568M, MIT, 8192 token. KHONG dung tien to.
    "bge-m3": ("BAAI/bge-m3", "", ""),
}


class LocalEmbedding:
    """Boc sentence-transformers, tu xu ly tien to."""

    def __init__(self, ten: str = "halong", device: str | None = None,
                 batch: int = 16):
        if ten not in MODEL:
            raise ValueError(
                "Khong biet model '" + ten + "'. Dang co: "
                + ", ".join(sorted(MODEL)))
        duong_dan, self._tt_hoi, self._tt_doan = MODEL[ten]
        self.ten = ten
        self.duong_dan = duong_dan
        self.batch = batch

        from sentence_transformers import SentenceTransformer
        # device=None de sentence-transformers tu chon. Tren may nay GPU chi
        # co 4GB va da do duoc la khong nap noi model sinh - nhung encoder
        # ~300M thi vua. Neu GPU khong dung duoc thi no tu lui ve CPU.
        self._m = SentenceTransformer(duong_dan, device=device)
        self.so_chieu = self._m.get_sentence_embedding_dimension()

    def ma_hoa(self, texts: list[str], *, la_cau_hoi: bool = False):
        if not texts:
            return np.zeros((0, self.so_chieu), dtype=np.float32)
        tt = self._tt_hoi if la_cau_hoi else self._tt_doan
        vao = [tt + t for t in texts] if tt else list(texts)
        v = self._m.encode(
            vao, batch_size=self.batch, convert_to_numpy=True,
            normalize_embeddings=True,      # de cosine = tich vo huong
            show_progress_bar=False)
        return v.astype(np.float32)
