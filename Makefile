# Supported hosts:
#   Windows  GNU Make + Git Bash + native Windows Python
#   Linux    GNU Make + Python 3.10+ (also WSL; a WSL checkout is a Linux host)
#   macOS    Apple make 3.81 or Homebrew gmake + Python 3.10+ (Intel and Apple Silicon)
# Keep this file LF-only (see .gitattributes); CRLF breaks recipes on Linux and macOS.
ifeq ($(OS),Windows_NT)
SHELL := bash
PYTHON ?= python
# `bash` must be Git Bash. C:\Windows\System32\bash.exe is the WSL launcher; if it comes
# first in PATH, recipes would run inside Linux against Windows paths.
BASH_KERNEL := $(shell bash -c "uname -s")
ifeq ($(filter MINGW% MSYS% CYGWIN%,$(BASH_KERNEL)),)
$(error Git Bash not found first in PATH, bash reports "$(BASH_KERNEL)". Install Git for Windows and put C:\Program Files\Git\bin before C:\Windows\System32 in PATH)
endif
else
# Prefer python3; fall back to a versioned interpreter when python3 is older than 3.10
# (macOS ships 3.9 with the Command Line Tools; Homebrew keg-only versions are versioned).
PYTHON_PICK := $(shell for p in python3 python3.14 python3.13 python3.12 python3.11 python3.10; do if command -v $$p >/dev/null 2>&1 && $$p -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then echo $$p; break; fi; done)
PYTHON ?= $(if $(PYTHON_PICK),$(PYTHON_PICK),python3)
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
.PHONY: help setup test release clean doctor
# Build dependencies are isolated from the host Python installation.
setup: $(VENV)/.ready
$(VENV)/.ready: pyproject.toml
	@$(PYTHON) -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10 or newer is required. macOS: brew install python. Windows: winget install Python.Python.3.13. Linux: install python3.10 or newer."'
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
		--name builder --paths src --copy-metadata feros-builder --distpath target/release \
		--workpath target/pyinstaller --specpath target src/main.py
	BUILDER="$(abspath $(BINARY))" "$(VENV_PYTHON)" scripts/check.py
	@mkdir -p "$(BIN_DIR)"
	@set -eu; staging=$$(mktemp -d "$(BIN_DIR)/.builder.XXXXXX"); \
		trap 'rm -rf "$$staging"' EXIT HUP INT TERM; \
		install -m 755 "$(BINARY)" "$$staging/$(BINARY_NAME)"; \
		"$$staging/$(BINARY_NAME)" help >/dev/null; \
		mv -f "$$staging/$(BINARY_NAME)" "$(BIN_DIR)/$(BINARY_NAME)"
	@printf 'FeROS Builder: ready at %s/$(BINARY_NAME)\n' "$(BIN_DIR)"
clean:
	rm -rf target
# Print the facts that differ between machines; compare output when a build behaves differently.
doctor:
	@printf 'Host        : %s/%s\n' "$(HOST_OS)" "$(HOST_ARCH)"
	@printf 'Interpreter : %s\n' "$(PYTHON)"
	@printf 'Python      : %s\n' "$$($(PYTHON) --version 2>&1)"
	@printf 'Make        : %s\n' "$(MAKE_VERSION)"
	@printf 'Shell       : %s\n' "$$(uname -s)"
	@printf 'Install dir : %s\n' "$(BIN_DIR)"
help:
	@printf 'FeROS Builder\n\n'
	@printf '  make setup    Prepare isolated build dependencies\n'
	@printf '  make test     Test the CLI, repositories, and image engine\n'
	@printf '  make release  Package, test, and install the host executable\n'
	@printf '  make clean    Remove target/; retain installed executables\n'
	@printf '  make doctor   Show host, interpreter, and tool versions\n'
	@printf '\nOverride BIN_ROOT to install into a shared workspace bin/.\n'