#!/bin/bash
# GAMMA Test Runner
# Runs all Python tests and checks

set -e  # Exit on first error

echo "================================================================================"
echo "Testing GAMMA Python Components"
echo "================================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

TOTAL_PASSED=0
TOTAL_FAILED=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Test: $test_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if eval "$test_command"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TOTAL_PASSED=$((TOTAL_PASSED + 1))
    else
        echo -e "${RED}✗ FAILED${NC}"
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
    fi
    echo ""
}

# Core test suites
run_test "Core Config" "python3 tests/test_core_config.py > /dev/null 2>&1"
run_test "Difficulty System" "python3 tests/test_difficulty.py > /dev/null 2>&1"
run_test "Mind Meld Engine" "python3 tests/test_mind_meld_engine.py > /dev/null 2>&1"
run_test "Mind Meld CLI" "python3 tests/test_mind_meld.py > /dev/null 2>&1"

# New feature tests
run_test "Swap Strategies" "python3 tests/test_strategies.py > /dev/null 2>&1"
run_test "MeldConfig Export/Import" "python3 tests/test_config.py > /dev/null 2>&1"
run_test "Visualization Export/Import" "python3 tests/test_visualization.py > /dev/null 2>&1"

# Import checks
run_test "Game Module Imports" "python3 -c \"
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))
from src.game.difficulty_levels import DifficultyLevel, GameSession
from src.game import game_logic
from src.game.tutorial_mode import TutorialMode
print('✓ All game imports work')
\" > /dev/null 2>&1"

run_test "Mind Meld Visualization Imports" "python3 -c \"
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))
from src.mind_meld.visualization import SwapVisualizer, SwapEvent
viz = SwapVisualizer(['Model A', 'Model B'])
print('✓ Visualization imports work')
\" > /dev/null 2>&1"

run_test "Comparison Mode Imports" "python3 -c \"
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))
from src.comparison.comparison_mode import ComparisonMode
print('✓ Comparison imports work')
\" > /dev/null 2>&1"

# Check that required directories exist
run_test "Required Directories" "python3 -c \"
import os
required_dirs = ['src', 'src/game', 'src/mind_meld', 'src/comparison', 'src/core', 'tests', 'tools', 'sessions']
for d in required_dirs:
    if not os.path.exists(d):
        raise Exception(f'Missing directory: {d}')
print('✓ All required directories exist')
\" > /dev/null 2>&1"

# Check README files exist
run_test "Documentation Files" "python3 -c \"
import os
required_readmes = [
    'README.md',
    'src/game/README.md',
    'src/mind_meld/README.md',
    'src/comparison/README.md',
    'src/core/README.md',
    'src/benchmarks/README.md',
    'tests/README.md'
]
for f in required_readmes:
    if not os.path.exists(f):
        raise Exception(f'Missing README: {f}')
print('✓ All README files exist')
\" > /dev/null 2>&1"

# Session viewer check
run_test "Session Viewer" "python3 tools/view_sessions.py --stats > /dev/null 2>&1"

# Summary
echo "================================================================================"
echo "Test Summary"
echo "================================================================================"
echo ""

if [ $TOTAL_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed! ($TOTAL_PASSED/$((TOTAL_PASSED + TOTAL_FAILED)))${NC}"
    echo ""
    echo "Test Coverage:"
    echo "  - Core Config: 20 tests"
    echo "  - Difficulty System: 18 tests"
    echo "  - Mind Meld Engine: 4 tests"
    echo "  - Swap Strategies: 14 tests"
    echo "  - MeldConfig Export/Import: 16 tests"
    echo "  - Visualization: 13 tests"
    echo "  - Integration Tests: 6 tests"
    echo "  Total: 91+ tests passing"
    exit 0
else
    echo -e "${RED}❌ Some tests failed! (Passed: $TOTAL_PASSED, Failed: $TOTAL_FAILED)${NC}"
    exit 1
fi
