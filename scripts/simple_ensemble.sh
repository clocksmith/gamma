#!/bin/bash
# Simple Token Ensembling Script for GAMMA Mind Meld
# Makes it easy to blend 2-3 models at the token level

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  GAMMA Simple Token Ensembling${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Activate virtual environment if not already active
if [ -z "$VIRTUAL_ENV" ]; then
    source .venv/bin/activate
fi

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Quick Examples:"
    echo "  $0 --preset fast                    # Use 2 small fast models"
    echo "  $0 --preset quality                 # Use 2 quality models (slower)"
    echo "  $0 --prompt \"Once upon a time\"     # Custom prompt"
    echo "  $0 --steps 20                       # Generate 20 tokens"
    echo ""
    echo "Options:"
    echo "  --preset fast|quality|diverse       Preset model combinations"
    echo "  --model1 ENGINE:MODEL               First model (e.g., pytorch:google/gemma-3-1b-it)"
    echo "  --model2 ENGINE:MODEL               Second model"
    echo "  --model3 ENGINE:MODEL               Optional third model"
    echo "  --prompt TEXT                       Starting prompt"
    echo "  --steps N                           Number of tokens to generate (default: 10)"
    echo "  --strategy NAME                     Blending strategy (default: weighted_average)"
    echo "  --help                              Show this help"
    echo ""
    echo "Blending Strategies:"
    echo "  weighted_average      - Simple average of all models (default, fast)"
    echo "  confidence_weighted   - Weight by confidence scores (smart)"
    echo "  dynamic_weighted      - Adapt weights based on performance"
    echo "  ensemble_voting       - Majority vote ensemble"
    echo ""
    exit 0
}

# Default values
PRESET=""
MODEL1=""
MODEL2=""
MODEL3=""
PROMPT="The quick brown fox"
STEPS=10
STRATEGY="weighted_average"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --preset)
            PRESET="$2"
            shift 2
            ;;
        --model1)
            MODEL1="$2"
            shift 2
            ;;
        --model2)
            MODEL2="$2"
            shift 2
            ;;
        --model3)
            MODEL3="$2"
            shift 2
            ;;
        --prompt)
            PROMPT="$2"
            shift 2
            ;;
        --steps)
            STEPS="$2"
            shift 2
            ;;
        --strategy)
            STRATEGY="$2"
            shift 2
            ;;
        --help|-h)
            show_usage
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            ;;
    esac
done

# Apply presets
if [ -n "$PRESET" ]; then
    case $PRESET in
        fast)
            MODEL1="pytorch:google/gemma-3-1b-it"
            MODEL2="pytorch:google/gemma-2-2b-it"
            echo -e "${GREEN}Using FAST preset:${NC}"
            echo "  • Gemma-3 1B (fastest, experimental)"
            echo "  • Gemma-2 2B (fast, stable)"
            ;;
        quality)
            MODEL1="pytorch:google/gemma-2-2b-it"
            MODEL2="pytorch:google/gemma-2-2b-it"
            echo -e "${GREEN}Using QUALITY preset:${NC}"
            echo "  • 2x Gemma-2 2B models"
            echo "  • Note: Same model twice for demonstration"
            ;;
        diverse)
            MODEL1="pytorch:google/gemma-3-1b-it"
            MODEL2="pytorch:google/gemma-2-2b-it"
            echo -e "${GREEN}Using DIVERSE preset:${NC}"
            echo "  • Gemma-3 1B"
            echo "  • Gemma-2 2B"
            ;;
        *)
            echo -e "${YELLOW}Unknown preset: $PRESET${NC}"
            show_usage
            ;;
    esac
fi

# Validate required parameters
if [ -z "$MODEL1" ] || [ -z "$MODEL2" ]; then
    echo -e "${YELLOW}Error: Must specify either --preset or both --model1 and --model2${NC}"
    show_usage
fi

# Build model list
MODELS="$MODEL1 $MODEL2"
if [ -n "$MODEL3" ]; then
    MODELS="$MODELS $MODEL3"
fi

# Display configuration
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo "  Prompt: \"$PROMPT\""
echo "  Steps: $STEPS tokens"
echo "  Strategy: $STRATEGY"
echo "  Models: $MODELS"
echo ""

# Run mind meld
echo -e "${GREEN}Starting token-level ensembling...${NC}"
echo ""

python gamma.py mind-meld \
    --models $MODELS \
    --use-blending \
    --blend-strategy "$STRATEGY" \
    --steps "$STEPS" \
    --prompt "$PROMPT" \
    --verbose

echo ""
echo -e "${GREEN}✅ Ensembling complete!${NC}"
