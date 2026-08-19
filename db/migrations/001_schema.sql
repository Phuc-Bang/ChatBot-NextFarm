-- 001_schema.sql — Lược đồ kho tri thức
-- Quy chuẩn v2.0 §25. Chạy bằng: python db/migrate.py
--
-- NGUYÊN TẮC XUYÊN SUỐT LƯỢC ĐỒ NÀY
--
--   1. Mọi chunk phải truy ngược được về URL gốc:
--        chunk -> document -> source -> url
--      Đây là cơ sở của citation và audit (§11, §20).
--
--   2. Hai luồng duyệt tách rời (DEC-020, §24):
--        document.approved  -> quyết định chunk có được index không
--        fact.verified      -> hàng rào kiểm số liệu + ground truth eval
--      Bảng fact KHÔNG phải nguồn cho retrieval.
--
--   3. Trạng thái duyệt sống trong git (knowledge/review/*.yaml).
--      Postgres là bản DẪN XUẤT, dựng lại được từ manifest + file duyệt.
--
--   4. Ràng buộc quan trọng được cài ở TẦNG DỮ LIỆU, không phải ở lời hứa
--      trong tài liệu. Xem các CONSTRAINT bên dưới và view indexable_chunk.

BEGIN;

-- ---------------------------------------------------------------------
-- source — một cơ quan / website nguồn
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS source (
    source_id       TEXT PRIMARY KEY,
    publisher       TEXT NOT NULL,
    base_url        TEXT,
    source_tier     SMALLINT NOT NULL CHECK (source_tier IN (1, 2)),
    region_default  TEXT,
    note            TEXT
);

COMMENT ON COLUMN source.source_tier IS
    'Chi 1 hoac 2. Tier 3 (blog, forum, SEO) bi cam o PoC nay - muc 22.1';

-- ---------------------------------------------------------------------
-- document — một tài liệu đã crawl
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS document (
    document_id     TEXT PRIMARY KEY,
    source_id       TEXT REFERENCES source(source_id) ON DELETE RESTRICT,
    url             TEXT NOT NULL,
    title           TEXT,
    crop            TEXT NOT NULL CHECK (crop IN ('lua', 'ca_chua', 'dua_chuot')),
    region          TEXT,

    -- NULL nghĩa là trang không ghi ngày. KHÔNG được đoán (§23.2).
    published_at    DATE,
    crawled_at      TIMESTAMPTZ NOT NULL,

    http_status     INTEGER,
    content_hash    TEXT,
    raw_path        TEXT,
    text_path       TEXT,
    doc_type        TEXT NOT NULL DEFAULT 'html' CHECK (doc_type IN ('html', 'pdf')),

    -- Cổng duyệt của luồng 1. Mặc định false: không duyệt thì không vào KB.
    approved        BOOLEAN NOT NULL DEFAULT FALSE,
    reviewer        TEXT,
    reviewed_at     TIMESTAMPTZ,
    reject_reason   TEXT,

    version         INTEGER NOT NULL DEFAULT 1,

    -- Đã duyệt thì phải biết AI duyệt và KHI NÀO. Không có thì không tính là
    -- đã duyệt — đây là điều kiện để audit được, không phải chi tiết hình thức.
    CONSTRAINT duyet_phai_co_nguoi_va_thoi_diem
        CHECK (approved = FALSE OR (reviewer IS NOT NULL AND reviewed_at IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS document_crop_idx     ON document (crop);
CREATE INDEX IF NOT EXISTS document_region_idx   ON document (region);
CREATE INDEX IF NOT EXISTS document_approved_idx ON document (approved);

COMMENT ON COLUMN document.approved IS
    'Cong duyet muc tai lieu (DEC-020 luong 1). Chi chunk cua tai lieu approved '
    'moi duoc nap vao vector DB.';

-- ---------------------------------------------------------------------
-- chunk — đơn vị truy xuất
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chunk (
    chunk_id            TEXT PRIMARY KEY,
    document_id         TEXT NOT NULL REFERENCES document(document_id) ON DELETE CASCADE,
    ordinal             INTEGER NOT NULL,

    text                TEXT NOT NULL,      -- nguyên văn, dùng cho evidence pack
    text_unaccent       TEXT NOT NULL,      -- bản bỏ dấu, dùng cho keyword search

    token_count         INTEGER,
    section_title       TEXT,
    crop                TEXT,
    region              TEXT,

    is_high_risk        BOOLEAN NOT NULL DEFAULT FALSE,
    reviewed_high_risk  BOOLEAN NOT NULL DEFAULT FALSE,
    approved            BOOLEAN NOT NULL DEFAULT TRUE,

    UNIQUE (document_id, ordinal),

    -- Chunk rủi ro cao (thuốc BVTV, liều lượng, nồng độ, thời gian cách ly)
    -- phải được duyệt LẺ TỪNG CHUNK trước khi được index (§24.4). Ràng buộc
    -- này làm cho việc quên duyệt trở thành lỗi ghi dữ liệu, không phải một
    -- sơ suất im lặng.
    CONSTRAINT high_risk_phai_duyet_le
        CHECK (NOT is_high_risk OR NOT approved OR reviewed_high_risk)
);

CREATE INDEX IF NOT EXISTS chunk_document_idx  ON chunk (document_id);
CREATE INDEX IF NOT EXISTS chunk_crop_idx      ON chunk (crop);
CREATE INDEX IF NOT EXISTS chunk_high_risk_idx ON chunk (is_high_risk) WHERE is_high_risk;

-- ---------------------------------------------------------------------
-- embedding
-- ---------------------------------------------------------------------
-- Cột vector cố ý KHÔNG khai số chiều: model embedding chưa được chọn
-- (DEC-015 = TODO, §26). Khi chốt model, migration sau sẽ ràng buộc số chiều
-- và tạo index ANN.
--
-- Đổi model bắt buộc phải re-embed toàn bộ, nên model_name và model_version
-- là BẮT BUỘC — không có version thì không biết vector nào đã cũ.
CREATE TABLE IF NOT EXISTS embedding (
    chunk_id        TEXT PRIMARY KEY REFERENCES chunk(chunk_id) ON DELETE CASCADE,
    vector          vector NOT NULL,
    dim             INTEGER NOT NULL,
    model_name      TEXT NOT NULL,
    model_version   TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS embedding_model_idx ON embedding (model_name, model_version);

-- ---------------------------------------------------------------------
-- fact — số liệu đã duyệt lẻ (luồng 2 của DEC-020)
-- ---------------------------------------------------------------------
-- KHÔNG phải nguồn cho retrieval. Ba việc bảng này gánh (§24.5):
--   a) kiểm số deterministic ở Grounding Validator tầng 2
--   b) ground truth cho tập kiểm thử — đáp án do NGƯỜI xác nhận
--   c) phát hiện mâu thuẫn giữa các nguồn
CREATE TABLE IF NOT EXISTS fact (
    fact_id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id     TEXT NOT NULL REFERENCES document(document_id) ON DELETE CASCADE,
    chunk_id        TEXT REFERENCES chunk(chunk_id) ON DELETE SET NULL,
    sentence_index  INTEGER NOT NULL,
    sentence        TEXT NOT NULL,          -- nguyên văn

    crop            TEXT,
    region          TEXT,
    metric          TEXT NOT NULL,

    -- Điền từ NGUYÊN VĂN câu. Không suy diễn, không quy đổi đơn vị (§27.3).
    value_min       NUMERIC,
    value_max       NUMERIC,
    unit            TEXT,
    stage           TEXT,

    high_risk       BOOLEAN NOT NULL DEFAULT FALSE,
    verified        BOOLEAN NOT NULL DEFAULT FALSE,
    reviewer        TEXT,
    reviewed_at     TIMESTAMPTZ,
    note            TEXT,

    UNIQUE (document_id, sentence_index),

    CONSTRAINT fact_duyet_phai_co_nguoi
        CHECK (verified = FALSE OR (reviewer IS NOT NULL AND reviewed_at IS NOT NULL)),

    -- Khoảng ngược (min > max) gần như luôn là lỗi nhập, và nếu lọt vào tầng
    -- kiểm số thì mọi con số đều "nằm ngoài khoảng" -> chặn nhầm hàng loạt.
    CONSTRAINT khoang_gia_tri_hop_le
        CHECK (value_min IS NULL OR value_max IS NULL OR value_min <= value_max)
);

CREATE INDEX IF NOT EXISTS fact_crop_metric_idx ON fact (crop, metric) WHERE verified;

-- ---------------------------------------------------------------------
-- query_log — audit, bắt buộc (§20, §38)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS query_log (
    query_id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ts                  TIMESTAMPTZ NOT NULL DEFAULT now(),

    question_raw        TEXT NOT NULL,
    question_normalized TEXT,

    intent              TEXT,
    intent_confidence   REAL,
    crop                TEXT,

    retrieved_chunk_ids TEXT[],
    evidence_pack       JSONB,
    llm_raw_output      JSONB,
    grounding_result    JSONB,

    final_answer        TEXT,
    abstained           BOOLEAN NOT NULL DEFAULT FALSE,
    abstain_reason      TEXT,

    -- Độ trễ TỪNG CHẶNG (§21.2) và số token (đầu vào cho mô hình chi phí §37.5).
    -- Ghi từ P7 chứ không đợi đến lúc cần báo cáo mới thêm.
    latency_ms          JSONB,
    token_in            INTEGER,
    token_out           INTEGER
);

CREATE INDEX IF NOT EXISTS query_log_ts_idx     ON query_log (ts DESC);
CREATE INDEX IF NOT EXISTS query_log_intent_idx ON query_log (intent);

COMMIT;
