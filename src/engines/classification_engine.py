#!/usr/bin/env python3
"""
Engine for Sequence Classification models, used by the Routing Mode.
"""

from typing import List, Dict, Any, Optional

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class SequenceClassificationEngine:
    """A simple engine to handle loading and running sequence classification models."""

    def __init__(self, model_name: str, engine_specific_config: Optional[Dict[str, Any]] = None):
        self.model_name = model_name
        self.engine_config = engine_specific_config or {}
        self.model: Optional[AutoModelForSequenceClassification] = None
        self.tokenizer: Optional[AutoTokenizer] = None
        self._device: Optional[torch.device] = None

    def load(self):
        """Load the tokenizer and model from Hugging Face."""
        device_map = self.engine_config.get("pytorch_device_map", "auto")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name, device_map=device_map)
        if self.model:
            self._device = self.model.device
        print(f"SequenceClassificationEngine: Model '{self.model_name}' loaded on device: {self._device}")

    def predict(self, texts: List[str]) -> List[float]:
        """Predict scores for a list of texts."""
        if not self.tokenizer or not self.model or not self._device:
            raise RuntimeError("Engine not fully loaded.")

        inputs = self.tokenizer(texts, return_tensors='pt', padding=True, truncation=True)
        inputs = {k: v.to(self._device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Assuming the "winning" score is in the last position of the logits
        # and applying softmax to get probabilities.
        scores = torch.softmax(outputs.logits, dim=-1)[:, -1].cpu().tolist()
        return scores
