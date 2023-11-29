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
	$(POETRY) run pyinstaller --onefile --clean --name observing_transcriber watcher.py --windowed
	cp settings.yaml dist/settings.yaml
build_github_actions:
	echo "cython<3.0" >> c.txt
	PIP_CONSTRAINT=c.txt pip install av==10.0.0
	pip install faster-whisper==0.10.0 watchfiles==0.21.0 asyncio==3.4.3 srt==3.5.3 pyinstaller==6.2.0
	pyinstaller --onefile --clean --name observing_transcriber watcher.py --windowed
	cp settings.yaml dist/settings.yaml
