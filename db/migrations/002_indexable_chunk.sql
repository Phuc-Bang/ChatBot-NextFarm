-- 002_indexable_chunk.sql — Cổng chặn ở tầng dữ liệu
--
-- Quy chuẩn v2.0 §25.2.
--
-- Nguyên tắc "human approval bắt buộc trước khi index" (DEC-005) không được
-- phép chỉ là một lời hứa trong tài liệu. View này biến nó thành ràng buộc
-- kỹ thuật: MỌI truy vấn retrieval chỉ được đọc từ indexable_chunk, không
-- bao giờ đọc thẳng bảng chunk.
--
-- Ba điều kiện, thiếu một là không được index:
--   1. Tài liệu đã được duyệt              (luồng 1 của DEC-020)
--   2. Chunk không bị đánh dấu loại
--   3. Chunk rủi ro cao phải được duyệt lẻ (§24.4)

BEGIN;

CREATE OR REPLACE VIEW indexable_chunk AS
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

COMMENT ON VIEW indexable_chunk IS
    'Cong chan cua DEC-005. Moi truy van retrieval chi duoc doc tu view nay. '
    'Doc thang bang chunk se lam lot chunk chua duyet vao cau tra loi.';

-- ---------------------------------------------------------------------
-- Chỉ mục cho tìm kiếm từ khoá tiếng Việt (DEC-021, §14.2)
-- ---------------------------------------------------------------------
-- PostgreSQL KHÔNG có cấu hình full-text search cho tiếng Việt trong bộ
-- stemmer đi kèm. Vì vậy dùng:
--   - config 'simple' trên cột đã bỏ dấu (không stem, chỉ tách token)
--   - trigram để chịu được lỗi chính tả và khớp câu hỏi không dấu
--
-- Cả hai đều đặt trên text_unaccent, nên câu hỏi "ca chua can dat ph bao nhieu"
-- khớp trực tiếp với bản bỏ dấu của chunk — không cần bước đoán dấu nào.
-- Đoán dấu là bịa; khớp trên bản bỏ dấu là tra cứu.

CREATE INDEX IF NOT EXISTS chunk_fts_simple_idx
    ON chunk USING GIN (to_tsvector('simple', text_unaccent));

CREATE INDEX IF NOT EXISTS chunk_trgm_idx
    ON chunk USING GIN (text_unaccent gin_trgm_ops);

COMMIT;
