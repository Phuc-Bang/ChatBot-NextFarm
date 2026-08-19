# ChatBot-NextFarm — Bài toán A
# Quy chuẩn: docs/NEXTFARM_PROBLEM_A_STANDARD_v2.0.md

.PHONY: help up down logs psql check-ext install install-crawler crawl extract test clean

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

test:
	python -m pytest tests/ -v

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
