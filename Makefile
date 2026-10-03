# Windows builds use GNU Make and Git Bash with native Windows Python.
ifeq ($(OS),Windows_NT)
SHELL := bash
PYTHON ?= python
else
PYTHON ?= python3
endif
BIN_ROOT ?= bin
VENV := .venv
HOST_OS := $(shell $(PYTHON) -c 'import platform; print(platform.system().lower())')
HOST_ARCH := $(shell $(PYTHON) -c 'import platform; print({"arm64": "aarch64", "amd64": "x86_64"}.get(platform.machine().lower(), platform.machine().lower()))')
ifeq ($(HOST_OS),windows)
VENV_PYTHON := $(VENV)/Scripts/python.exe
EXE_EXT := .exe
else
VENV_PYTHON := $(VENV)/bin/python
EXE_EXT :=
endif
BINARY_NAME := builder$(EXE_EXT)
BINARY := target/release/$(BINARY_NAME)
BIN_DIR := $(BIN_ROOT)/$(HOST_OS)/$(HOST_ARCH)
.DEFAULT_GOAL := help
.DELETE_ON_ERROR:
.PHONY: help setup test release clean
# Build dependencies are isolated from the host Python installation.
setup: $(VENV)/.ready
$(VENV)/.ready: pyproject.toml
	@$(PYTHON) -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10 or newer is required"'
	$(PYTHON) -m venv "$(VENV)"
	"$(VENV_PYTHON)" -m pip install -e '.[build]'
	@touch "$@"
test:
	$(PYTHON) scripts/check.py
# Validate both source execution and the frozen executable before publication.
release: setup
	@case "$(HOST_OS)/$(HOST_ARCH)" in \
		darwin/aarch64|darwin/x86_64|linux/aarch64|linux/x86_64|windows/x86_64) ;; \
		*) printf 'Unsupported build host: %s/%s\n' "$(HOST_OS)" "$(HOST_ARCH)" >&2; exit 1 ;; \
	esac
	"$(VENV_PYTHON)" scripts/check.py
	"$(VENV_PYTHON)" -m PyInstaller --noconfirm --clean --onefile \
		--name builder --paths src --distpath target/release \
		--workpath target/pyinstaller --specpath target src/main.py
	BUILDER="$(abspath $(BINARY))" "$(VENV_PYTHON)" scripts/check.py
	@mkdir -p "$(BIN_DIR)"
	@set -eu; staging=$$(mktemp -d "$(BIN_DIR)/.builder.XXXXXX"); \
		trap 'rm -rf "$$staging"' EXIT HUP INT TERM; \
		install -m 755 "$(BINARY)" "$$staging/$(BINARY_NAME)"; \
		"$$staging/$(BINARY_NAME)" --help >/dev/null; \
		mv -f "$$staging/$(BINARY_NAME)" "$(BIN_DIR)/$(BINARY_NAME)"
	@printf 'FeROS Builder: ready at %s/$(BINARY_NAME)\n' "$(BIN_DIR)"
clean:
	rm -rf target
help:
	@printf 'FeROS Builder\n\n'
	@printf '  make setup    Prepare isolated build dependencies\n'
	@printf '  make test     Test the image CLI with synthetic inputs\n'
	@printf '  make release  Package, test, and install the host executable\n'
	@printf '  make clean    Remove target/; retain installed executables\n'
	@printf '\nOverride BIN_ROOT to install into a shared workspace bin/.\n'
