#!/usr/bin/env bash
# GAMMA test runner.
# Thin wrapper over pytest with full failure output.
# No arguments: core smoke tests. Full suite: ./run_tests.sh tests

set -euo pipefail

# An explicit interpreter is authoritative; never silently cross environments.
if [[ -z "${PYTHON_BIN:-}" ]]; then
  if [[ -x ".venv/bin/python" ]]; then
    PYTHON_BIN=".venv/bin/python"
  else
    PYTHON_BIN="python3"
  fi
fi

if ! "${PYTHON_BIN}" -m pytest --version >/dev/null 2>&1; then
  echo "[run_tests] pytest is not available for ${PYTHON_BIN}."
  echo "[run_tests] install it with: ${PYTHON_BIN} -m pip install pytest"
  exit 1
fi

if [[ "$#" -gt 0 ]]; then
  TARGETS=("$@")
else
  TARGETS=(
    "tests/test_engine_interface.py"
    "tests/test_engine_factory.py"
    "tests/test_game.py"
    "tests/test_ui_components.py"
  )
fi

PYTEST_ARGS=("-x" "-ra")
if [[ -n "${PYTEST_EXTRA_ARGS:-}" ]]; then
  # shellcheck disable=SC2206
  EXTRA=( ${PYTEST_EXTRA_ARGS} )
  PYTEST_ARGS+=("${EXTRA[@]}")
fi

echo "[run_tests] python: ${PYTHON_BIN}"
echo "[run_tests] pytest ${PYTEST_ARGS[*]} ${TARGETS[*]}"

exec "${PYTHON_BIN}" -m pytest "${PYTEST_ARGS[@]}" "${TARGETS[@]}"
