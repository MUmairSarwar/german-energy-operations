.PHONY: setup analyse test dashboard
setup:
	python -m pip install -r requirements-lock.txt
	python -m pip install --no-deps -e .
analyse:
	python -m energy_ops.pipeline
test:
	python -m pytest -q
dashboard:
	python -m streamlit run app.py
