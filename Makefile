fmt:
	ruff format .

check:
	ruff check .
	ruff format --check .

install:
	pip install -r requirements.txt -r requirements-dev.txt
