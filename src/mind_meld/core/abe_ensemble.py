"""
Agreement-Based Ensembling (ABE) for Mind Meld.

ABE combines predictions from multiple LLMs by finding token combinations
where the resulting text strings "agree" (one is a prefix of the other).
"""

import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ABECandidate:
    """Represents a candidate token combination for ABE."""
    model_tokens: List[Tuple[int, str]]  # (token_id, token_text) for each model
    combined_score: float
    agreed_text: str
    is_complete: bool  # True if all models have generated same length


class ABEEnsemble:
    """
    Implements Agreement-Based Ensembling for multiple models.
    """
    
    def __init__(self, models: List[Any], verbose: bool = False):
        self.models = models
        self.verbose = verbose
        self.model_positions = [0] * len(models)  # Track each model's position in generated text
        self.stalled_models = set()  # Models that need to catch up
        
    def find_agreement(
        self, 
        all_probs: List[np.ndarray],
        temperature: float = 1.0,
        top_k: int = 10
    ) -> ABECandidate:
        """
        Find the best token combination where models agree.
        
        Args:
            all_probs: Probability distributions from each model
            temperature: Temperature for sampling
            top_k: Number of top tokens to consider from each model
            
        Returns:
            The best agreed-upon token combination
        """
        candidates = []
        
        # Get top-k tokens from each model
        model_top_tokens = []
        for model_idx, (model, probs) in enumerate(zip(self.models, all_probs)):
            # Apply temperature
            if temperature != 1.0:
                probs = np.power(probs, 1.0 / temperature)
                probs = probs / np.sum(probs)
            
            # Get top-k indices and their probabilities
            top_k_indices = np.argsort(probs)[-top_k:][::-1]
            top_tokens = []
            
            for idx in top_k_indices:
                token_text = model.decode([idx], skip_special_tokens=False)
                if token_text:  # Skip empty tokens
                    top_tokens.append((idx, token_text, probs[idx]))
            
            model_top_tokens.append(top_tokens)
        
        # Search for agreements between all model pairs
        for i, tokens_i in enumerate(model_top_tokens):
            for token_i_idx, token_i_text, prob_i in tokens_i:
                for j, tokens_j in enumerate(model_top_tokens):
                    if i >= j:  # Skip duplicate pairs
                        continue
                        
                    for token_j_idx, token_j_text, prob_j in tokens_j:
                        # Check if tokens agree (one is prefix of the other)
                        agreed_text = self._check_agreement(token_i_text, token_j_text)
                        
                        if agreed_text is not None:
                            # Calculate combined score
                            combined_score = np.sqrt(prob_i * prob_j)  # Geometric mean
                            
                            # Create candidate for all models
                            model_tokens = []
                            total_score = 0
                            
                            for k, model in enumerate(self.models):
                                if k == i:
                                    model_tokens.append((token_i_idx, token_i_text))
                                    total_score += prob_i
                                elif k == j:
                                    model_tokens.append((token_j_idx, token_j_text))
                                    total_score += prob_j
                                else:
                                    # Find best matching token for other models
                                    best_match = self._find_best_match(
                                        agreed_text, model_top_tokens[k]
                                    )
                                    if best_match:
                                        model_tokens.append((best_match[0], best_match[1]))
                                        total_score += best_match[2]
                                    else:
                                        # No match found, use empty token
                                        model_tokens.append((0, ""))
                            
                            # Check if all models generated same length
                            lengths = [len(t[1]) for t in model_tokens]
                            is_complete = len(set(lengths)) == 1
                            
                            candidates.append(ABECandidate(
                                model_tokens=model_tokens,
                                combined_score=total_score / len(self.models) if len(self.models) > 0 else 0,
                                agreed_text=agreed_text,
                                is_complete=is_complete
                            ))
        
        # If no agreement found, use highest probability token from first model
        if not candidates:
            if self.verbose:
                print("  [ABE] No agreement found, using highest probability token")
            
            best_token = model_top_tokens[0][0]  # First model's best token
            model_tokens = [(best_token[0], best_token[1])]
            
            # Find similar tokens in other models
            for k in range(1, len(self.models)):
                best_match = self._find_best_match(best_token[1], model_top_tokens[k])
                if best_match:
                    model_tokens.append((best_match[0], best_match[1]))
                else:
                    model_tokens.append((0, ""))
            
            return ABECandidate(
                model_tokens=model_tokens,
                combined_score=best_token[2],
                agreed_text=best_token[1],
                is_complete=False
            )
        
        # Sort candidates by score and return best
        candidates.sort(key=lambda c: c.combined_score, reverse=True)
        
        if self.verbose and candidates:
            best = candidates[0]
            print(f"  [ABE] Agreement found: '{best.agreed_text}' (score: {best.combined_score:.3f})")
            for i, (token_id, token_text) in enumerate(best.model_tokens):
                print(f"    Model {i}: '{token_text}' (id: {token_id})")
        
        return candidates[0]
    
    def _check_agreement(self, text1: str, text2: str) -> Optional[str]:
        """
        Check if two text strings agree (one is prefix of the other).
        Returns the agreed text or None if no agreement.
        """
        # Clean texts (remove special tokens if needed)
        text1 = text1.strip()
        text2 = text2.strip()
        
        if not text1 or not text2:
            return None
        
        # Check if one is a prefix of the other
        if text1.startswith(text2):
            return text2  # Return shorter one
        elif text2.startswith(text1):
            return text1  # Return shorter one
        
        # Check for partial overlap (e.g., " the" vs "the")
        if text1.lstrip().startswith(text2.lstrip()):
            return text2
        elif text2.lstrip().startswith(text1.lstrip()):
            return text1
        
        return None
    
    def _find_best_match(
        self, 
        target_text: str, 
        token_list: List[Tuple[int, str, float]]
    ) -> Optional[Tuple[int, str, float]]:
        """
        Find the best matching token for a target text from a list of tokens.
        """
        target_text = target_text.strip()
        
        for token_id, token_text, prob in token_list:
            if self._check_agreement(token_text, target_text) is not None:
                return (token_id, token_text, prob)
        
        return None
    
    def update_positions(self, candidate: ABECandidate):
        """
        Update model positions based on the selected candidate.
        Handles stalling of models that generated shorter tokens.
        """
        self.stalled_models.clear()
        
        # Find the longest token length
        max_length = max(len(t[1]) for t in candidate.model_tokens)
        
        # Update positions and identify stalled models
        for i, (token_id, token_text) in enumerate(candidate.model_tokens):
            self.model_positions[i] += len(token_text)
            
            if len(token_text) < max_length:
                self.stalled_models.add(i)
                if self.verbose:
                    print(f"  [ABE] Model {i} stalled (generated shorter token)")
    
    def ensemble_step(
        self,
        all_probs: List[np.ndarray],
        temperature: float = 1.0,
        top_k: int = 10
    ) -> Tuple[str, List[int]]:
        """
        Perform one step of ABE ensemble generation.
        
        Returns:
            Tuple of (agreed_text, list of token_ids for each model)
        """
        # Find best agreement
        candidate = self.find_agreement(all_probs, temperature, top_k)
        
        # Update model positions
        self.update_positions(candidate)
        
        # Return the agreed text and token IDs
        token_ids = [t[0] for t in candidate.model_tokens]
        
        return candidate.agreed_text, token_ids