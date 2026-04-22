.PHONY: up down build logs shell-backend shell-ollama pull-model test-api clean

# ─── Start / Stop ────────────────────────────────────────────────────────────
up:
	docker compose up --build -d
	@echo ""
	@echo "✅  Stack is starting up..."
	@echo "   UI:      http://localhost:8501"
	@echo "   API:     http://localhost:8000/docs"
	@echo "   Ollama:  http://localhost:11434"
	@echo ""
	@echo "⏳  Waiting for Ollama model download (first run ~5 min)..."
	@docker compose logs -f ollama-init

down:
	docker compose down

build:
	docker compose build --no-cache

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f esg-backend

logs-ui:
	docker compose logs -f esg-ui

# ─── Shells ──────────────────────────────────────────────────────────────────
shell-backend:
	docker exec -it esg_backend bash

shell-ollama:
	docker exec -it esg_ollama bash

# ─── Model management ────────────────────────────────────────────────────────
pull-model:
	docker exec esg_ollama ollama pull $(MODEL)

list-models:
	docker exec esg_ollama ollama list

# ─── Test ────────────────────────────────────────────────────────────────────
test-api:
	@echo "Testing health endpoint..."
	curl -s http://localhost:8000/health | python3 -m json.tool
	@echo ""
	@echo "Submitting sample audit..."
	curl -s -X POST http://localhost:8000/audit/start \
	  -H "Content-Type: application/json" \
	  -d '{"company_name":"Acme Corp","report_text":"$(shell cat data/sample_reports/acme_esg_2024.txt | head -c 2000 | tr '\''\"'\'' '\''\'\''  )","report_year":"2024"}' \
	  | python3 -m json.tool

# ─── Cleanup ─────────────────────────────────────────────────────────────────
clean:
	docker compose down -v
	rm -rf reports/*.pdf