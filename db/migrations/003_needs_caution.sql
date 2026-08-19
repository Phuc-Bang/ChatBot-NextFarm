-- 003_needs_caution.sql — Tách nội dung rủi ro thành hai mức
--
-- Quy chuẩn v2.0 §19 case C4 và §24.4 mô tả hai nghĩa vụ khác nhau:
--
--   a) Chunk chứa thuốc BVTV / hoạt chất / liều lượng / nồng độ / thời gian
--      cách ly  ->  PHẢI DUYỆT LẺ TỪNG CHUNK trước khi index (is_high_risk)
--   b) Chunk nói về sâu bệnh nói chung  ->  câu trả lời dùng chunk này BẮT
--      BUỘC kèm cảnh báo, nhưng không cần duyệt lẻ (needs_caution)
--
-- Bản đầu gộp chung một cờ, khiến 96/292 chunk thật phải duyệt lẻ (33%).
-- Đo lại với danh sách hẹp: 34 chunk (12%). Chênh lệch do "sâu bệnh" và
-- "phòng trừ" — hai từ chỉ chủ đề, gần như tài liệu canh tác nào cũng có.
-- Bắt duyệt lẻ 96 chunk tiêu mất ~1,6 giờ trong ngân sách ~10 giờ của đội
-- một người mà không đổi lại an toàn tương xứng.

BEGIN;

ALTER TABLE chunk ADD COLUMN IF NOT EXISTS needs_caution BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN chunk.is_high_risk IS
    'Chua thuoc/hoat chat/lieu luong/nong do/cach ly -> phai duyet le tung chunk (muc 24.4)';
COMMENT ON COLUMN chunk.needs_caution IS
    'Cau tra loi dung chunk nay bat buoc kem canh bao (muc 19 case C4). '
    'Khong bat buoc duyet le.';

-- Chunk rủi ro cao thì đương nhiên cũng phải kèm cảnh báo
UPDATE chunk SET needs_caution = TRUE WHERE is_high_risk;

ALTER TABLE chunk DROP CONSTRAINT IF EXISTS rui_ro_cao_thi_luon_canh_bao;
ALTER TABLE chunk ADD CONSTRAINT rui_ro_cao_thi_luon_canh_bao
    CHECK (NOT is_high_risk OR needs_caution);

-- View phải phát cờ này ra ngoài để tầng trả lời biết khi nào cần cảnh báo
DROP VIEW IF EXISTS indexable_chunk;
CREATE VIEW indexable_chunk AS
SELECT
    c.chunk_id,
    c.document_id,
    c.ordinal,
    c.text,
    c.text_unaccent,
    c.token_count,
    c.section_title,
    COALESCE(c.crop, d.crop)     AS crop,
    COALESCE(c.region, d.region) AS region,
    c.is_high_risk,
    c.needs_caution,
    d.url,
    d.title        AS document_title,
    d.published_at,
    d.source_id,
    s.publisher,
    s.source_tier
FROM chunk c
JOIN document d ON d.document_id = c.document_id
LEFT JOIN source s ON s.source_id = d.source_id
WHERE d.approved = TRUE
  AND c.approved = TRUE
  AND (c.is_high_risk = FALSE OR c.reviewed_high_risk = TRUE);

COMMIT;
