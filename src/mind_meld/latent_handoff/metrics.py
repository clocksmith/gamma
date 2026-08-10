"""Tensor, logit, behavioral, and timing metrics for handoff evidence."""

from __future__ import annotations

import torch

from .contract import ContractError
from .ridge import coefficient_of_determination


def normalized_mse(actual: torch.Tensor, predicted: torch.Tensor) -> float:
    if actual.shape != predicted.shape:
        raise ContractError("normalized MSE inputs differ in shape")
    numerator = torch.mean((actual.float() - predicted.float()) ** 2)
    denominator = torch.mean(actual.float() ** 2).clamp_min(torch.finfo(torch.float32).eps)
    return float((numerator / denominator).item())


def cosine_similarity(actual: torch.Tensor, predicted: torch.Tensor) -> float:
    if actual.shape != predicted.shape:
        raise ContractError("cosine inputs differ in shape")
    a = actual.float().reshape(-1, actual.shape[-1])
    b = predicted.float().reshape(-1, predicted.shape[-1])
    return float(torch.nn.functional.cosine_similarity(a, b, dim=-1).mean().item())


def tensor_fidelity(actual: torch.Tensor, predicted: torch.Tensor) -> dict[str, float]:
    return {
        "r2": coefficient_of_determination(
            actual.reshape(-1, actual.shape[-1]), predicted.reshape(-1, predicted.shape[-1])
        ),
        "normalizedMse": normalized_mse(actual, predicted),
        "cosine": cosine_similarity(actual, predicted),
    }


def logit_fidelity(native: torch.Tensor, candidate: torch.Tensor, top_k: int = 5) -> dict[str, float]:
    if native.shape != candidate.shape:
        raise ContractError("logit inputs differ in shape")
    native_logp = torch.log_softmax(native.float(), dim=-1)
    candidate_logp = torch.log_softmax(candidate.float(), dim=-1)
    native_p = native_logp.exp()
    candidate_p = candidate_logp.exp()
    midpoint = 0.5 * (native_p + candidate_p)
    kl = torch.sum(native_p * (native_logp - candidate_logp), dim=-1).mean()
    js = 0.5 * (
        torch.sum(native_p * (native_logp - midpoint.log()), dim=-1)
        + torch.sum(candidate_p * (candidate_logp - midpoint.log()), dim=-1)
    ).mean()
    native_top = native.topk(min(top_k, native.shape[-1]), dim=-1).indices
    candidate_top = candidate.topk(min(top_k, candidate.shape[-1]), dim=-1).indices
    top_k_overlap = (
        (native_top.unsqueeze(-1) == candidate_top.unsqueeze(-2)).any(dim=-1).float().mean()
    )
    native_top_token = native.argmax(dim=-1, keepdim=True)
    native_top_logp = native_logp.gather(-1, native_top_token)
    candidate_native_top_logp = candidate_logp.gather(-1, native_top_token)
    return {
        "klDivergence": float(kl.item()),
        "jensenShannonDivergence": float(js.item()),
        "top1Agreement": float((native.argmax(-1) == candidate.argmax(-1)).float().mean().item()),
        "topKOverlap": float(top_k_overlap.item()),
        "nativeTopTokenLogProbabilityGap": float(
            (native_top_logp - candidate_native_top_logp).mean().item()
        ),
    }


def floor_normalized_retention(score: float, native: float, floor: float) -> float:
    if native <= floor:
        raise ContractError("native score must exceed its chance floor")
    return (score - floor) / (native - floor)


def teacher_forced_perplexity(logits: torch.Tensor, token_ids: torch.Tensor) -> float:
    """Score continuation tokens 2..N from identical teacher-forced inputs."""

    if logits.ndim != 3 or token_ids.ndim != 2 or logits.shape[:2] != token_ids.shape:
        raise ContractError("teacher-forced logits and tokens are not aligned")
    if token_ids.shape[1] < 2:
        raise ContractError("teacher-forced continuation requires at least two tokens")
    losses = torch.nn.functional.cross_entropy(
        logits[:, :-1, :].float().reshape(-1, logits.shape[-1]),
        token_ids[:, 1:].reshape(-1),
        reduction="mean",
    )
    return float(torch.exp(losses).item())


def exact_recall(expected: str, actual: str) -> float:
    return float(expected == actual)
