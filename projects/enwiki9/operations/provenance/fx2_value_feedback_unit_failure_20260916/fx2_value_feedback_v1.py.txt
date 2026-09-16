"""Exact reference for a proposed attention-value error-feedback mutation.

This is a mathematical kernel, not an integrated compressor. The arithmetic
bounds concern a fixed sequence and fixed weights, not final code length.
"""
from fractions import Fraction
import math
import struct

Q = 65536
HALF = Q // 2
MINIMUM = -128 * Q
MAXIMUM = 127 * Q


def normalized_q16(bits):
    value = struct.unpack('<f', struct.pack('<I', bits))[0]
    if not math.isfinite(value):
        raise ValueError('nonfinite value')
    value = max(Fraction(-128), min(Fraction(127), Fraction(value)))
    return round(value * Q)


def step(value, previous):
    if type(value) is not int or type(previous) is not int:
        raise ValueError('integer coordinates required')
    if not MINIMUM <= value <= MAXIMUM or not -HALF <= previous <= HALF:
        raise ValueError('outside declared integer domain')
    total = value + previous
    quantized = max(-128, min(127, round(Fraction(total, Q))))
    return quantized, total - quantized * Q


def sequence(values, initial=0):
    residuals = [initial]
    quantized = []
    for value in values:
        q, residual = step(value, residuals[-1])
        quantized.append(q)
        residuals.append(residual)
    return quantized, residuals


def weighted_certificate(values, quantized, residuals, weights):
    """Check the exact telescoping identity; bound a fixed weighted sum."""
    n = len(values)
    if not n or len(quantized) != n or len(weights) != n or len(residuals) != n + 1:
        raise ValueError('misaligned sequence')
    if any(abs(r) > HALF for r in residuals):
        raise ValueError('unbounded residual')
    for i in range(n):
        if step(values[i], residuals[i]) != (quantized[i], residuals[i + 1]):
            raise ValueError('not this feedback trajectory')
    weights = list(map(Fraction, weights))
    error = sum((w * (q - Fraction(v, Q)) for w, q, v in
                 zip(weights, quantized, values)), Fraction())
    identity = (weights[0] * residuals[0] - weights[-1] * residuals[-1]
                + sum((weights[i + 1] - weights[i]) * residuals[i + 1]
                      for i in range(n - 1))) / Q
    variation = sum(abs(weights[i + 1] - weights[i]) for i in range(n - 1))
    boundary = abs(weights[-1]) + (abs(weights[0]) if residuals[0] else 0)
    bound = (variation + boundary) / 2
    assert error == identity and abs(error) <= bound
    return dict(error=error, bound=bound,
                q16_input_rounding_allowance=sum(map(abs, weights)) / (2 * Q))
