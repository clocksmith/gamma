# Engine Tests

This directory contains tests for LLM engine implementations.

## Structure

```
tests/engines/
├── conftest.py              # Shared fixtures and test utilities
├── base_engine_test.py      # Base test class for common engine behavior
├── test_sampling_utils_phase1.py  # Tests for Phase 1 refactoring
└── test_*_engine.py         # Engine-specific tests
```

## Running Tests

Run all engine tests:
```bash
python3 -m pytest tests/engines/ -v
```

Run a specific engine test:
```bash
python3 -m pytest tests/engines/test_pytorch_engine.py -v
```

Run with coverage:
```bash
python3 -m pytest tests/engines/ --cov=src/engines --cov-report=html
```

## Test Fixtures

### conftest.py Fixtures

- `mock_tokenizer`: Mock HuggingFace tokenizer (doesn't require model download)
- `mock_model_output()`: Factory for creating mock model outputs
- `test_prompts`: Common test prompts
- `engine_config`: Default engine configuration
- `sampling_params`: Default sampling parameters

### Helper Functions

- `assert_valid_prediction_output(output)`: Verify prediction output structure
- `assert_valid_tokenizer(tokenizer)`: Verify tokenizer has required attributes

## Writing Engine Tests

### Option 1: Use BaseEngineTest

Inherit from `BaseEngineTest` to get common test patterns:

```python
from tests.engines.base_engine_test import BaseEngineTest
from src.engines.my_engine import MyEngine

class TestMyEngine(BaseEngineTest):
    def create_engine(self, config=None):
        return MyEngine("test-model", config)

    def mock_model_loading(self, engine, mock_tokenizer, mock_model_output):
        # Mock the model loading to avoid downloads
        engine.tokenizer = mock_tokenizer
        engine.model = Mock()
        # Add engine-specific mocking here
```

This gives you these tests for free:
- `test_engine_initialization`
- `test_config_helpers`
- `test_encode_decode_cycle`
- `test_vocabulary_size`
- `test_token_text_retrieval`
- `test_kv_cache_reset`
- `test_special_token_map`
- `test_prediction_output_structure`
- `test_sampling_with_different_temperatures`
- `test_top_k_filtering`
- `test_top_p_filtering`
- `test_get_probabilities_at_step`
- `test_attention_visualization`

### Option 2: Write Custom Tests

For engine-specific functionality:

```python
import pytest
from src.engines.my_engine import MyEngine

def test_custom_feature(mock_tokenizer):
    engine = MyEngine("test-model")
    engine.tokenizer = mock_tokenizer
    # Test engine-specific features
    assert engine.custom_method() == expected_value
```

## Mocking Strategy

### Why Mock Model Loading?

- **Speed**: Tests run in milliseconds instead of minutes
- **Reproducibility**: Same results every time
- **No Network**: Tests work offline
- **No Disk**: No need to download multi-GB models

### How to Mock

**PyTorch Example:**
```python
from unittest.mock import Mock, patch

def mock_model_loading(engine, mock_tokenizer, mock_model_output):
    engine.tokenizer = mock_tokenizer

    # Mock the model
    engine.model = Mock()
    engine.model.eval = Mock()
    engine.model.to = Mock(return_value=engine.model)

    # Mock forward pass
    def mock_forward(**kwargs):
        return mock_model_output(framework="torch")
    engine.model.__call__ = mock_forward
```

**TensorFlow Example:**
```python
def mock_model_loading(engine, mock_tokenizer, mock_model_output):
    engine.tokenizer = mock_tokenizer
    engine.model = Mock()

    def mock_call(input_ids, **kwargs):
        return mock_model_output(framework="tf")
    engine.model.__call__ = mock_call
```

## Test Coverage Goals

| Module | Target Coverage | Status |
|--------|----------------|--------|
| pytorch_engine.py | 80%+ | ⏳ In Progress |
| tensorflow_engine.py | 80%+ | ⏳ In Progress |
| jax_engine.py | 80%+ | ⏳ In Progress |
| mlx_engine.py | 80%+ | ⏳ In Progress |
| onnx_engine.py | 80%+ | ⏳ In Progress |
| llama_cpp_engine.py | 80%+ | ⏳ In Progress |
| ollama_engine.py | 80%+ | ⏳ In Progress |
| sampling_utils.py | 95%+ | ✅ Complete |

## Best Practices

1. **Test Behavior, Not Implementation**: Focus on what the engine does, not how
2. **Use Fixtures**: Leverage shared fixtures to reduce duplication
3. **Mock External Dependencies**: Never download real models in tests
4. **Test Edge Cases**: Empty inputs, invalid parameters, error conditions
5. **Fast Tests**: All engine tests should run in < 5 seconds total
6. **Descriptive Names**: Test names should explain what they verify
7. **Assertions**: Use specific assertions with helpful error messages

## Debugging Failed Tests

Run with verbose output:
```bash
python3 -m pytest tests/engines/test_my_engine.py -vv
```

Run a single test:
```bash
python3 -m pytest tests/engines/test_my_engine.py::test_specific_function -v
```

Drop into debugger on failure:
```bash
python3 -m pytest tests/engines/test_my_engine.py --pdb
```

## Phase 1 Refactoring Tests

Tests in `test_sampling_utils_phase1.py` verify the Phase 1 refactoring work:
- `get_top_k_tokens()` consolidation
- `process_logits_pipeline()` functionality
- Temperature/top-k/top-p filtering

All 15 tests pass, validating the refactoring maintains correctness.
