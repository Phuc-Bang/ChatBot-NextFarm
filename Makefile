# ChatBot-NextFarm — Bài toán A
# Quy chuẩn: docs/NEXTFARM_PROBLEM_A_STANDARD_v2.0.md

.PHONY: help up down logs psql check-ext install install-crawler crawl extract ingest duyet-chunk duyet-chunk-status smoke eval-tu-choi c0 c1 c2 recall rerank risk-coverage tang3 phieu-cham serve test clean

help:
	@echo "Các lệnh có sẵn:"
	@echo "  make up              - Khởi động PostgreSQL + pgvector"
	@echo "  make down            - Dừng và gỡ container"
	@echo "  make logs            - Xem log database"
	@echo "  make psql            - Mở psql trong container"
	@echo "  make check-ext       - Kiểm tra 3 extension bắt buộc (DoD của P0)"
	@echo "  make install         - Cài phụ thuộc cho app"
	@echo "  make install-crawler - Cài phụ thuộc cho crawler"
	@echo "  make crawl           - Chạy crawler (P1)"
	@echo "  make extract         - Trích câu chứa số liệu (P2)"
	@echo "  make ingest          - Dựng lại kho tri thức từ file trong git (P5)"
	@echo ""
	@echo "  make smoke           - Thử LLM 3 câu TRƯỚC khi chạy 222 case"
	@echo "  make eval-tu-choi    - Đo tầng từ chối (không cần model)"
	@echo "  make recall          - Đo Recall@K, chọn model embedding (P6)"
	@echo "  make c0              - Baseline: LLM trần (P4)"
	@echo "  make c1              - RAG, không guardrail (P7)"
	@echo "  make c2              - RAG + guardrail — cấu hình sản phẩm (P8)"
	@echo "  make rerank          - Đo đóng góp riêng của reranker (bật/tắt)"
	@echo "  make tang3           - Đo Grounding tầng 3 trên kết quả C2 đã có"
	@echo "  make risk-coverage   - Đường risk–coverage, chốt ngưỡng (mục 30.4)"
	@echo "  make phieu-cham      - Sinh phiếu chấm cho chuyên gia (mục 32)"
	@echo ""
	@echo "  make serve           - Chạy API + hai trang giao diện"
	@echo "  make test            - Chạy toàn bộ kiểm thử"
	@echo "  make clean           - Xoá cache Python"

up:
	docker compose up -d
	@echo "Đang đợi database sẵn sàng..."
	@docker compose exec -T db sh -c 'until pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB; do sleep 1; done'
	@echo "Database đã sẵn sàng."

down:
	docker compose down

logs:
	docker compose logs -f db

psql:
	docker compose exec db psql -U nextfarm -d nextfarm

# Điều kiện hoàn thành của P0: phải thấy đủ vector, unaccent, pg_trgm
check-ext:
	@docker compose exec -T db psql -U nextfarm -d nextfarm -tAc \
		"SELECT extname FROM pg_extension WHERE extname IN ('vector','unaccent','pg_trgm') ORDER BY extname;"

install:
	python -m pip install -r requirements.txt

install-crawler:
	python -m pip install -r crawler/requirements.txt

crawl:
	cd crawler && python crawl.py

extract:
	cd crawler && python extract.py

ingest:
	python knowledge/ingestion/load.py

# Luồng 3 của DEC-020: duyệt lẻ chunk rủi ro cao (thuốc BVTV, liều lượng).
# Hỏi từng cái một, không có đường tắt duyệt hàng loạt.
duyet-chunk:
	python knowledge/review/review_chunks.py --limit 10

duyet-chunk-status:
	python knowledge/review/review_chunks.py --status

# Chạy cái này TRƯỚC khi tốn 222 case: gemini-1.5-flash đã bị Google tắt hẳn,
# phát hiện ở câu thứ 1 tốn 3 giây, phát hiện ở câu 200 tốn cả buổi.
smoke:
	python scripts/smoke_llm.py

eval-tu-choi:
	python evaluation/runners/eval_tu_choi.py

recall:
	python evaluation/runners/eval_retrieval.py --models halong e5-small --hybrid halong

# --nghi 1.5: free tier rất chặt, chạy liên tục là đụng trần 429.
c0:
	python evaluation/runners/run_c0.py --nghi 1.5

c1:
	python evaluation/runners/run_c1.py --nghi 1.5

c2:
	python evaluation/runners/run_c2.py --nghi 1.5

rerank:
	python evaluation/runners/eval_rerank.py

# Chay duoc KHONG can quota: tang 3 mac dinh thuan quy tac.
tang3:
	python evaluation/runners/c2_them_tang3.py

# Can chay lai C2 truoc, de co truong diem_cao_nhat va intent_do_tin_cay.
risk-coverage:
	python evaluation/runners/risk_coverage.py

phieu-cham:
	python evaluation/tools/sinh_phieu_cham.py

serve:
	@echo "  http://localhost:8000        trang chat"
	@echo "  http://localhost:8000/admin  trang quản trị"
	python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

test:
	python -m pytest tests/ -q

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
