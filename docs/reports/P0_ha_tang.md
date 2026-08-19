# P0 — Kiểm chứng hạ tầng

> Bằng chứng cho điều kiện hoàn thành của P0. Ghi lại để không phải tin vào lời kể.

## Môi trường

| Hạng mục | Giá trị đo được |
|---|---|
| Docker | 29.5.3 |
| Docker Compose | v5.1.4 |
| Ảnh database | `pgvector/pgvector:pg16` |
| Hệ điều hành | Windows 11 |

## Ba extension bắt buộc (DEC-021)

Lệnh:

```bash
make up
make check-ext
```

Kết quả:

```
pg_trgm   1.6
plpgsql   1.0
unaccent  1.1
vector    0.8.6
```

✅ Đủ cả ba extension bắt buộc: `vector`, `unaccent`, `pg_trgm`.

## Kiểm chứng cơ chế truy vấn không dấu

Đây là cơ chế giải bài toán A4 (hiểu sai tiếng Việt) ở tầng dữ liệu, thay vì
để LLM đoán dấu — xem quy chuẩn v2.0 mục 14.3.

```sql
SELECT immutable_unaccent('Cà chua cần đất pH bao nhiêu');
```

Kết quả:

```
Ca chua can dat pH bao nhieu
```

Hàm được bọc thành `IMMUTABLE` nên tạo được index biểu thức — đã kiểm:

```sql
CREATE TEMP TABLE t(x text);
CREATE INDEX ON t (immutable_unaccent(x));
-- CREATE INDEX
```

✅ Câu hỏi không dấu của nông dân sẽ khớp trực tiếp với bản bỏ dấu của chunk,
không cần bước đoán dấu nào.

## Chưa làm ở P0

- Lược đồ bảng (`source`, `document`, `chunk`, ...) — thuộc P5
- View `indexable_chunk` — thuộc P5
- Index GIN trigram trên dữ liệu thật — thuộc P5
