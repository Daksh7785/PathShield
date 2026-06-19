.PHONY: setup install db-init train infer demo test clean stop

setup: install db-init
	@echo "✓ Setup complete"

install:
	pip install -r requirements.txt

db-init:
	python scripts/seed_database.py

train:
	bash scripts/run_training.sh

infer:
	bash scripts/process_city.sh bengaluru

demo:
	python scripts/demo_setup.py
	@echo "Starting services..."
	uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
	streamlit run dashboard/app.py --server.port 8501 &
	@echo "✓ Dashboard: http://localhost:8501"
	@echo "✓ API docs:  http://localhost:8000/docs"

test:
	python -m pytest tests/ -v --tb=short

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

stop:
	pkill -f uvicorn || true
	pkill -f streamlit || true
