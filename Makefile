POETRY := $(shell command -v poetry 2> /dev/null)

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Please use 'make <target>' where <target> is one of"
	@echo ""
	@echo "  install     install packages and prepare environment"
	@echo ""
	@echo "Check the Makefile to know exactly what each target is doing."

install:
	@if [ -z $(POETRY) ]; then echo "Poetry could not be found. See https://python-poetry.org/docs/"; exit 2; fi
	$(POETRY) install

run:
	$(POETRY) run python watcher.py

build_exe:
	$(POETRY) run pyinstaller --onefile --clean --name observing_transcriber watcher.py --add-data "settings.yaml:."
	cp settings.yaml dist/settings.yaml