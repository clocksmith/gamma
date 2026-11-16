"""Streaming centered ridge regression used by directional KV mappers."""

from __future__ import annotations

from dataclasses import dataclass

import torch

from .contract import ContractError


@dataclass
class RidgeAccumulator:
    input_dim: int
    output_dim: int
    dtype: torch.dtype = torch.float64

    def __post_init__(self) -> None:
        if self.input_dim <= 0 or self.output_dim <= 0:
            raise ContractError("ridge dimensions must be positive")
        self.count = 0
        self.sum_x = torch.zeros(self.input_dim, dtype=self.dtype)
        self.sum_y = torch.zeros(self.output_dim, dtype=self.dtype)
        self.sum_y_square = torch.zeros(self.output_dim, dtype=self.dtype)
        self.xtx = torch.zeros((self.input_dim, self.input_dim), dtype=self.dtype)
        self.xty = torch.zeros((self.input_dim, self.output_dim), dtype=self.dtype)

    def update(self, x: torch.Tensor, y: torch.Tensor) -> None:
        if x.ndim != 2 or y.ndim != 2 or x.shape[0] != y.shape[0]:
            raise ContractError("ridge observations must be X[N,F], Y[N,D]")
        if x.shape[1] != self.input_dim or y.shape[1] != self.output_dim:
            raise ContractError("ridge observation dimensions do not match accumulator")
        x_cpu = x.detach().to(device="cpu", dtype=self.dtype)
        y_cpu = y.detach().to(device="cpu", dtype=self.dtype)
        self.count += x_cpu.shape[0]
        self.sum_x += x_cpu.sum(dim=0)
        self.sum_y += y_cpu.sum(dim=0)
        self.sum_y_square += y_cpu.square().sum(dim=0)
        self.xtx += x_cpu.T @ x_cpu
        self.xty += x_cpu.T @ y_cpu

    def solve(self, ridge_lambda: float) -> tuple[torch.Tensor, torch.Tensor]:
        if self.count == 0:
            raise ContractError("cannot solve ridge regression without observations")
        if ridge_lambda < 0:
            raise ContractError("ridge lambda must be non-negative")
        mean_x = self.sum_x / self.count
        mean_y = self.sum_y / self.count
        centered_xtx = self.xtx - self.count * torch.outer(mean_x, mean_x)
        centered_xty = self.xty - self.count * torch.outer(mean_x, mean_y)
        regularized = centered_xtx + ridge_lambda * torch.eye(
            self.input_dim, dtype=self.dtype
        )
        try:
            weight = torch.linalg.solve(regularized, centered_xty)
        except torch.linalg.LinAlgError:
            weight = torch.linalg.lstsq(regularized, centered_xty).solution
        bias = mean_y - mean_x @ weight
        return weight.to(torch.float32), bias.to(torch.float32)

    def r2_by_output(self, weight: torch.Tensor) -> torch.Tensor:
        """Compute calibration R2 from sufficient statistics only."""

        if self.count == 0 or weight.shape != (self.input_dim, self.output_dim):
            raise ContractError("ridge R2 requires a solved, shape-matched accumulator")
        mean_x = self.sum_x / self.count
        mean_y = self.sum_y / self.count
        centered_xtx = self.xtx - self.count * torch.outer(mean_x, mean_x)
        centered_xty = self.xty - self.count * torch.outer(mean_x, mean_y)
        weight = weight.to(self.dtype)
        total = self.sum_y_square - self.count * mean_y.square()
        cross = (weight * centered_xty).sum(dim=0)
        predicted_square = (weight * (centered_xtx @ weight)).sum(dim=0)
        residual = total - 2.0 * cross + predicted_square
        exact_constant = (total == 0) & (residual.abs() < torch.finfo(self.dtype).eps)
        safe_total = torch.where(total == 0, torch.ones_like(total), total)
        score = 1.0 - residual / safe_total
        return torch.where(total == 0, exact_constant.to(self.dtype), score)


def coefficient_of_determination(actual: torch.Tensor, predicted: torch.Tensor) -> float:
    if actual.shape != predicted.shape or actual.numel() == 0:
        raise ContractError("R2 inputs must be non-empty and shape-matched")
    actual = actual.detach().to(torch.float64)
    predicted = predicted.detach().to(torch.float64)
    residual = torch.sum((actual - predicted) ** 2)
    centered = torch.sum((actual - actual.mean(dim=0, keepdim=True)) ** 2)
    if centered == 0:
        return 1.0 if residual == 0 else 0.0
    return float((1.0 - residual / centered).item())
