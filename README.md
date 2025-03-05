# GGJJ (Gemma Gamma Jemma Jamma)

An interactive educational game that demystifies transformer-based language models through gameplay.

## Overview

GGJJ is a hands-on tool that lets you peer inside Google's Gemma language model to see how it thinks and predicts text. By turning complex AI concepts into a guessing game, GGJJ makes advanced machine learning techniques accessible and fun to explore.

### Demos

Playing locally wih gemma-2b-it on a Macbook air.

#### Screenshots

<img width="1076" alt="1" src="https://github.com/user-attachments/assets/ee54cda4-772f-4d99-b6f3-1bc5d9c3b2de" />
<img width="1080" alt="2" src="https://github.com/user-attachments/assets/3d6c98f9-2373-495e-895d-417b1929ccf3" />
<img width="1078" alt="3" src="https://github.com/user-attachments/assets/8852b962-7c68-4fcc-baa3-1ed0a45955b3" />
<img width="1079" alt="4" src="https://github.com/user-attachments/assets/9441ebef-ff37-47e4-81ca-6da89a4400fb" />
<img width="1084" alt="5" src="https://github.com/user-attachments/assets/39d518b2-3f6b-4484-87b6-f03dea4e3be9" />

#### Video

https://github.com/user-attachments/assets/96aa4b78-8899-4b22-8b59-435b21c21ba0

## Transformer Steps Visualized in the Game

The game captures many steps in the transformer architecture. Here's how each highlighted step is represented in GGJJ:

1. Tokenization: ✨ *Input text is tokenized when you enter your prompt, with token IDs shown in debug mode*

2. Embedding Lookup: *Not directly visualized*

3. Positional Encoding: *Not directly visualized*

4. **Query/Key/Value Matrix Multiplications**: ✨ *Visualized through the attention heatmap display that shows which tokens influence others*
   - The game shows which input tokens receive most attention when predicting the next token
   - Attention scores represent the result of Q-K dot products after softmax normalization

5. **Attention Mechanism**: ✨ *Explicitly visualized as color-coded heatmaps*
   - Darker colors indicate higher attention weights between tokens
   - Normalized scores (0-1) show relative importance of each input token
   - The visualization shows attention from the final layer, averaged across all heads

6. **Raw Logits Generation**: ✨ *Displayed as the first set of token probabilities*
   - Shows the unfiltered probability distribution over the entire vocabulary
   - Demonstrates what the model initially predicts before any sampling techniques

7. **Temperature Scaling**: ✨ *Explicitly shown in second probability display*
   - Demonstrates how adjusting temperature changes the probability distribution
   - Higher temperatures flatten the distribution, lower ones make it more peaked
   - The game uses temperature = 0.7 by default

8. **Top-K Filtering**: ✨ *Visualized in third probability display*
   - Shows how only the K most probable tokens are kept
   - The game uses top-k = 8 by default
   - Illustrates how this narrows the distribution to only likely candidates

9. **Top-P (Nucleus) Sampling**: ✨ *Visualized in fourth probability display*
   - Shows tokens remaining after filtering to the top p% of probability mass
   - The game uses top-p = 0.95 by default
   - Demonstrates how this creates a dynamic cutoff based on probability distribution

10. **Token Selection/Sampling**: ✨ *Central to the game's guessing mechanic*
    - Players try to predict which tokens will be selected
    - The game shows the top-ranked tokens after all filtering steps
    - Players see how sampling strategies affect final token selection

11. **Autoregressive Generation**: ✨ *Experienced throughout gameplay*
    - Each newly predicted token becomes part of the input for the next step
    - The game shows how the context grows with each prediction
    - Demonstrates how the model builds coherent text one token at a time

## Background

Modern language models use transformer architectures to process and generate text. These models work by predicting the next token in a sequence based on all previous tokens. The prediction process involves several key steps:

1. Tokenizing input text into numerical representations
2. Computing attention scores between tokens (which tokens "attend" to which others)
3. Generating a probability distribution over possible next tokens
4. Applying sampling techniques (temperature, top-k, top-p) to select the final token

GGJJ makes these abstract processes tangible by letting you compete against the model's predictions and visualizing the attention patterns that drive token selection.

## How to Play

1. Start the game and enter a beginning sentence or phrase
2. The model will show you several possible continuations
3. Try to guess which sequence of tokens the model will rank highest
4. After guessing, see how the model arrived at its decision through:
   - Attention visualizations (which words influenced predictions most)
   - Probability distributions at various stages of filtering
   - Step-by-step explanations of the model's reasoning
5. The game continues with the model's chosen tokens added to the sequence
6. Repeat until you complete all rounds or the model generates an end-of-sequence token

Your score is based on how often your predictions match the model's choices.

## Setup and Installation

### Requirements

- Python 3.8+
- PyTorch
- Transformers library
- (Optional) colorama for better Windows terminal support

### Basic Installation

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate

# Install required packages
pip install torch transformers
pip install colorama  # Recommended for Windows users
```

### Running the Game

```bash
# Run the game with default settings
python ggjj.py
```

### Accessing Gemma Models

You'll need access to Google's Gemma models to run this game. There are several options:

1. **Hugging Face (Recommended)**: 
   - Visit [Hugging Face's Gemma page](https://huggingface.co/google/gemma-2b)
   - Accept the terms and conditions
   - Generate a Hugging Face token and set it in your environment:
     ```bash
     export HUGGING_FACE_HUB_TOKEN=your_token_here
     ```

2. **Google AI Studio**:
   - Access the models through [Google AI Studio](https://ai.google.dev/)
   - Use Google's Python SDK to download and use the models locally

3. **Kaggle**:
   - Gemma models are available on Kaggle for use in notebooks

## Complete Transformer Architecture Steps

Here is a comprehensive list of all transformer steps, with the ones visualized in the game highlighted:

1. **Tokenization (Software)**: ✨ *Input text → tokens (integer IDs)*

2. Embedding Lookup (Software & Hardware): Token IDs → embedding vectors.

3. Positional Encoding Generation (Software/Hardware): Create positional encoding vectors.

4. Positional Encoding Addition (Hardware): Add encodings to embeddings.

5. **Encoder Query Weight Matrix Multiplication (Hardware)**: ✨ *Input × W^Q. Visible in attention visualization*

6. **Encoder Key Weight Matrix Multiplication (Hardware)**: ✨ *Input × W^K. Visible in attention visualization*

7. **Encoder Value Weight Matrix Multiplication (Hardware)**: ✨ *Input × W^V. Visible in attention visualization*

8. **Query-Key Matrix Multiplication (Hardware)**: ✨ *QK^T. Raw attention scores shown in heatmap*

9. **Scaling (Hardware)**: ✨ *QK^T / √d_k. Normalized attention scores shown in visualization*

10. Padding Mask Creation (Encoder) (Software): Create padding mask.

11. Padding Mask Application (Encoder) (Hardware): Add mask to scaled QK^T.

12. **Softmax (Encoder Self-Attention) (Hardware)**: ✨ *Softmax(masked, scaled QK^T). Visualized in attention heatmap*

13. **Attention-Value Matrix Multiplication (Hardware)**: ✨ *Softmax output × V. Final effect visible in token predictions*

14. Multi-Head Concatenation (Hardware): Concatenate attention head outputs.

15. Multi-Head Output Projection (Hardware): Concatenated output × W^O.

16. Residual Addition (Encoder) (Hardware): Original input + attention output.

17. Layer Normalization (Encoder) (Hardware): Normalize the result.

18. Feed-Forward Layer 1 (Encoder) (Hardware): Normalized output × weight matrix.

19. Add Bias 1 (Encoder FFN)(Hardware): Adds the first bias vector.

20. Activation (Encoder) (Hardware): Apply activation (e.g., GeLU).

21. Feed-Forward Layer 2 (Encoder) (Hardware): Activated output × weight matrix.

22. Add Bias 2 (Encoder FFN)(Hardware): Adds the second bias term.

23. Residual Addition (Encoder) (Hardware): Feed-forward input + output.

24. Layer Normalization (Encoder) (Hardware): Normalize.

25. Decoder Input Embedding (Software & Hardware): Start token or previous tokens → embeddings.

26. **Decoder Query Weight Matrix Multiplication (Hardware)**: ✨ *Similar to Step 5, but for decoder. Captured in logits generation*

27. **Decoder Key Weight Matrix Multiplication (Hardware)**: ✨ *Similar to Step 6, but for decoder. Captured in logits generation*

28. **Decoder Value Weight Matrix Multiplication (Hardware)**: ✨ *Similar to Step 7, but for decoder. Captured in logits generation*

29. **Query-Key Matrix Multiplication (Decoder) (Hardware)**: ✨ *Similar to Step 8, but for decoder. Captured in logits generation*

30. **Scaling (Decoder) (Hardware)**: ✨ *Similar to Step 9, but for decoder. Captured in logits generation*

31. **Attention Mask Creation (Decoder) (Software)**: ✨ *Create attention mask for autoregressive masking. Implicitly used in autoregressive generation*

32. Padding Mask Creation (Decoder) (Software): Create padding mask if needed.

33. **Mask Application (Decoder) (Hardware)**: ✨ *Add attention + padding masks to scaled QK^T. Implicitly used in autoregressive generation*

34. **Softmax (Decoder Self-Attention) (Hardware)**: ✨ *Softmax(masked, scaled QK^T). Raw logits shown in probability display*

35. **Attention-Value Matrix Multiplication (Decoder) (Hardware)**: ✨ *Softmax output × Value matrix. Affects final token probabilities*

36. Multi-Head Concatenation (Decoder) (Hardware): Similar to Step 14, but for decoder.

37. Multi-Head Output Projection (Decoder) (Hardware): Similar to Step 15, but for decoder.

38. Residual Addition (Decoder Self-Attention) (Hardware): Decoder input + attention output.

39. Layer Normalization (Decoder Self-Attention) (Hardware): Normalize.

40. Encoder Output Key Multiplication (Hardware): Final encoder output × Key weight matrix (Encoder-Decoder attention).

41. Encoder Output Value Multiplication (Hardware): Final encoder output × Value weight matrix (Encoder-Decoder attention).

42. Decoder Query - Encoder Key Multiplication (Hardware): Q (decoder) × K (encoder).

43. Scaling (Encoder-Decoder Attention)(Hardware): Divide by √d_k.

44. Padding Mask Application (Encoder-Decoder Attention) (Hardware): Add encoder padding mask.

45. Softmax (Encoder-Decoder Attention) (Hardware): Apply softmax.

46. Attention-Value Multiplication (Encoder-Decoder Attention) (Hardware): Softmax output × Value matrix (encoder).

47. Multi-Head Concatenation (Encoder-Decoder Attention) (Hardware): Concatenate heads.

48. Multi-Head Output Projection (Encoder-Decoder Attention) (Hardware): Project output.

49. Residual Addition (Encoder-Decoder Attention) (Hardware): Add to input.

50. Layer Normalization (Encoder-Decoder Attention) (Hardware): Normalize.

51. Feed-Forward Layer 1 (Decoder) (Hardware): FFN first layer.

52. Add Bias 1 (Decoder FFN)(Hardware): Add first bias.

53. Activation (Decoder) (Hardware): Apply activation.

54. Feed-Forward Layer 2 (Decoder) (Hardware): FFN second layer.

55. Add Bias 2 (Decoder FFN)(Hardware): Add second bias.

56. Residual Addition (Decoder FFN) (Hardware): Add to input.

57. Layer Normalization (Decoder FFN) (Hardware): Normalize.

58. **Final Logits Projection**: ✨ *Projecting hidden states to vocabulary. Raw logits displayed in game*

59. **Temperature Scaling**: ✨ *Adjusting probability distribution sharpness. Explicitly visualized in separate probability display*

60. **Top-K Filtering**: ✨ *Keeping only K most probable tokens. Explicitly visualized in separate probability display*

61. **Top-P (Nucleus) Sampling**: ✨ *Filtering based on cumulative probability. Explicitly visualized in separate probability display*

62. **Final Token Selection**: ✨ *Selecting the next token based on filtered distribution. Central to the guessing game mechanic*

## TODO: Future Enhancements

These items will be moved to the issue tracker:

### Bugs
- [ ] Fix timers that are all using same start time
- [ ] Investigate major slowdown at ~50 encoding steps on 2b model
- [ ] Fix spacing issues when printing sentence
- [ ] Replace confusing comma-separated choices with vertical list or pipe separator

### Feature Requests
- [ ] Add more detailed attention statistics and visualizations
- [ ] Continue generation to EOS token after max_encoding_steps for game
- [ ] Add keyboard shortcut "qqq" to auto-insert EOS token
- [ ] Add highlighting for current sentence in attention visualization
- [ ] Add toggle for verbose/minimal print statements
- [ ] Allow option to use player-guessed word rather than LLM's choice
- [ ] Provide more information in look-ahead (tree of probabilities)
- [ ] Give more context about which part of forward feed attention step is active
- [ ] Add visuals for encoding steps happening in parallel
- [ ] Use commutative property of multiplication examples instead of RNN examples
- [ ] Create web-based version with interactive visualizations
- [ ] Support more model architectures beyond Gemma
- [ ] Add comparative analysis between different models
- [ ] Implement multi-step lookahead to show branching probabilities
- [ ] Add user-adjustable parameters for sampling techniques
