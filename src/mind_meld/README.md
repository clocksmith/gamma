# Mind Meld Mode (EXPERIMENTAL)

A revolutionary mode that allows multiple language models to collaborate during text generation by dynamically swapping their neural states mid-sentence. This creates a unique "mind meld" effect where models can combine their strengths and produce outputs that neither could generate alone.

#### Quick Start

```bash
# Standalone CLI with interactive menu
python src/mind_meld/mind_meld.py

# Quick start with default Gemma models
python src/mind_meld/mind_meld.py --enhanced --blend

# Run from main game
python game.py --meld --meld-models pytorch:google/gemma-3-1b-it pytorch:google/gemma-2-2b-it
```

#### How Mind Meld Works

**Core Concept:** Mind Meld enables real-time collaboration between multiple LLMs by:
1. **Token-Level Swapping:** Models take turns generating tokens based on configurable strategies
2. **State Transfer:** Attempts to bridge internal states (KV cache) between models for context preservation
3. **Vocabulary Alignment:** Translates probability distributions between different tokenizer vocabularies
4. **Optional Blending:** Instead of hard swapping, can blend outputs from multiple models smoothly

#### Swap Strategies

- **Pattern-Based:** Swap at punctuation marks (., !, ?, etc.)
- **Fixed Interval:** Swap every N tokens
- **Round Robin:** Swap every single token
- **Confidence-Based:** Swap when model confidence drops below threshold
- **Random:** Swap with configurable probability
- **Attention-Guided:** Swap based on attention patterns

#### Enhanced Features (NEW)

Enable advanced capabilities with `--enhanced` flag:

##### 1. Vocabulary Alignment Strategies
- **Hybrid:** Combines multiple alignment methods for best results
- **Intersection:** Only use tokens common to all models
- **Fuzzy:** Approximate matching for similar tokens
- **Subword:** Break tokens into smaller units for alignment
- **Semantic:** Meaning-based token matching

##### 2. Logit Blending
Instead of hard swapping, blend model outputs smoothly:
- **Weighted Average:** Smooth probability blending
- **Confidence Weighted:** Trust confident models more
- **Dynamic Weighted:** Learn optimal weights over time
- **Ensemble Voting:** Combine top predictions from each model

##### 3. Statistics Tracking
- Real-time contribution percentages
- Swap pattern analysis
- Confidence and perplexity tracking
- Export to JSON for analysis

##### 4. KV Cache Projection
Advanced bridging for incompatible model architectures:
- Projection matrices for dimension matching
- Attention head alignment
- Layer count adaptation
- Pattern preservation

#### Examples

```bash
# Basic Mind Meld with pattern-based swapping
python src/mind_meld/mind_meld.py --models pytorch:google/gemma-2b pytorch:google/gemma-2b-it --strategy pattern

# Enhanced mode with confidence-weighted blending
python src/mind_meld/mind_meld.py --enhanced --blend --blend-strategy confidence_weighted

# Fixed interval swapping every 3 tokens
python src/mind_meld/mind_meld.py --strategy fixed --interval 3

# Round-robin (alternating every token)
python src/mind_meld/mind_meld.py --strategy round_robin

# Track statistics and save to file
python src/mind_meld/mind_meld.py --enhanced --stats-file meld_stats.json

# Custom vocabulary alignment
python src/mind_meld/mind_meld.py --enhanced --alignment semantic
```

#### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `--enhanced` | Enable advanced features | False |
| `--blend` | Use logit blending instead of swapping | False |
| `--strategy` | Swap strategy (pattern/fixed/round_robin/etc) | pattern |
| `--interval` | Tokens between swaps (fixed strategy) | 5 |
| `--blend-strategy` | How to blend logits | weighted_average |
| `--alignment` | Vocabulary alignment method | hybrid |
| `--stats-file` | Save statistics to JSON | None |
| `--temperature` | Generation temperature | 0.7 |
| `--top-k` | Top-K filtering | 8 |
| `--top-p` | Top-P (nucleus) filtering | 0.95 |

#### Technical Details

**Architecture Components:**
- `MeldEngine`: Orchestrates model swapping and state management
- `VocabularyAligner`: Handles token vocabulary differences
- `LogitBlender`: Implements smooth output blending
- `KVCacheProjectionBridge`: Bridges incompatible model architectures
- `StatisticsTracker`: Monitors model contributions and performance

**Challenges Addressed:**
- **Vocabulary Mismatch:** Different models use different tokenizers
- **Architecture Incompatibility:** Models have different dimensions/layers
- **Context Preservation:** Maintaining coherent state across swaps
- **Smooth Transitions:** Avoiding jarring changes in output style

#### Limitations

- KV cache bridging works best between similar architectures
- Some model combinations may reset context on swap
- Vocabulary alignment can introduce slight probability shifts
- Performance overhead from running multiple models

#### Use Cases

- **Creative Writing:** Combine creative and analytical models
- **Style Transfer:** Blend formal and casual language models
- **Capability Fusion:** Merge specialized models (code + prose)
- **Model Comparison:** See how different models approach the same context
- **Research:** Study model behavior and interaction patterns