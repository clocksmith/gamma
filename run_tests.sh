#!/usr/bin/env bash
# GAMMA test runner.
# Thin wrapper over pytest with full failure output.

set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
fi

if ! "${PYTHON_BIN}" -m pytest --version >/dev/null 2>&1; then
  if [[ "${PYTHON_BIN}" != "python3" ]] && python3 -m pytest --version >/dev/null 2>&1; then
    echo "[run_tests] pytest not available in ${PYTHON_BIN}; falling back to python3"
    PYTHON_BIN="python3"
  else
    echo "[run_tests] pytest is not installed for ${PYTHON_BIN}."
    echo "[run_tests] install it with: ${PYTHON_BIN} -m pip install pytest"
    exit 1
  fi
fi

if [[ "$#" -gt 0 ]]; then
  TARGETS=("$@")
else
  TARGETS=("tests")
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
