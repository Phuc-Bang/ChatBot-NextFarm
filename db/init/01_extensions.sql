-- Ba extension bat buoc theo quy chuan v2.0 muc 14.2 (DEC-021).
--
--   vector    : luu va tim kiem embedding (muc 12)
--   unaccent  : bo dau tieng Viet -> phuc vu cau hoi khong dau
--   pg_trgm   : so khop gan dung -> chiu duoc loi chinh ta
--
-- LUU Y: PostgreSQL KHONG co cau hinh full-text search cho tieng Viet
-- trong bo stemmer di kem. Vi vay keyword search dung config 'simple'
-- tren cot text_unaccent, khong dung to_tsvector('vietnamese', ...).

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- unaccent() mac dinh la STABLE nen khong dung truc tiep trong index duoc.
-- Boc lai thanh ham IMMUTABLE de co the tao index bieu thuc khi can.
CREATE OR REPLACE FUNCTION immutable_unaccent(text)
RETURNS text
LANGUAGE sql
IMMUTABLE
PARALLEL SAFE
STRICT
AS $$ SELECT public.unaccent('public.unaccent'::regdictionary, $1) $$;
