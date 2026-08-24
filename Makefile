PYTHON := $(shell pyenv which python)
PYTEST  := $(shell pyenv which pytest)

.PHONY: test lint

test:
	$(PYTEST) --cov=app --cov=services --cov=managers --cov-fail-under=80 -v

lint:
	pre-commit run --all-files
