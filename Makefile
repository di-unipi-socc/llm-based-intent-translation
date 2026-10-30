.PHONY: install data serve

install:
	uv sync --locked --all-groups

data:
	uv run --locked python scripts/export_data.py

serve:
	uv run --locked python -m http.server 8000 --directory docs
