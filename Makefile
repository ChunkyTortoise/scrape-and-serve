.PHONY: demo test lint clean setup generate-data

demo:
	streamlit run app.py

test:
	python -m pytest tests/ -v

lint:
	ruff check scrape_and_serve/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true
	rm -rf .pytest_cache .ruff_cache

setup:
	pip install -r requirements-dev.txt

generate-data:
	python demo_data/generate_demo_data.py
