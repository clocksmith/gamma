"""
Shared CLI argument definitions for GAMMA commands.

This module consolidates common argument definitions to prevent drift
between different CLI tools (game, mind-meld, comparison, benchmark).

Usage:
    from src.core.cli_args import add_sampling_args, add_model_args

    parser = argparse.ArgumentParser()
    add_sampling_args(parser)
    add_model_args(parser)
"""

import argparse
from dataclasses import dataclass
from typing import Optional

from src.core import config as cfg
from src.engines.capability_registry import list_engines

# ============================================================================
# Default Values (single source of truth)
# ============================================================================

@dataclass(frozen=True)
class SamplingDefaults:
    """Default values for sampling parameters."""
    temperature: float = cfg.DEFAULT_TEMPERATURE
    top_k: int = cfg.DEFAULT_TOP_K
    top_p: float = cfg.DEFAULT_TOP_P


@dataclass(frozen=True)
class GenerationDefaults:
    """Default values for generation parameters."""
    steps: int = cfg.DEFAULT_MAX_DECODE_STEPS
    max_tokens: int = 100


SAMPLING_DEFAULTS = SamplingDefaults()
GENERATION_DEFAULTS = GenerationDefaults()


# ============================================================================
# Argument Group Builders
# ============================================================================

def add_sampling_args(
    parser: argparse.ArgumentParser,
    defaults: Optional[SamplingDefaults] = None
) -> argparse._ArgumentGroup:
    """Add temperature, top-k, and top-p sampling arguments.

    Args:
        parser: ArgumentParser to add arguments to
        defaults: Optional custom defaults (uses SAMPLING_DEFAULTS if None)

    Returns:
        The argument group for chaining
    """
    defaults = defaults or SAMPLING_DEFAULTS

    group = parser.add_argument_group('Sampling Parameters')
    group.add_argument(
        '--temperature', '-t',
        type=float,
        default=defaults.temperature,
        metavar='FLOAT',
        help=f'Sampling temperature (higher = more random, default: {defaults.temperature})'
    )
    group.add_argument(
        '--top-k', '-k',
        type=int,
        default=defaults.top_k,
        metavar='INT',
        help=f'Top-K sampling limit (0 = disabled, default: {defaults.top_k})'
    )
    group.add_argument(
        '--top-p', '-p',
        type=float,
        default=defaults.top_p,
        metavar='FLOAT',
        help=f'Top-P (nucleus) sampling threshold (default: {defaults.top_p})'
    )
    return group


def add_generation_args(
    parser: argparse.ArgumentParser,
    defaults: Optional[GenerationDefaults] = None
) -> argparse._ArgumentGroup:
    """Add generation step/token arguments.

    Args:
        parser: ArgumentParser to add arguments to
        defaults: Optional custom defaults

    Returns:
        The argument group for chaining
    """
    defaults = defaults or GENERATION_DEFAULTS

    group = parser.add_argument_group('Generation Parameters')
    group.add_argument(
        '--steps', '-s',
        type=int,
        default=defaults.steps,
        metavar='INT',
        help=f'Number of generation steps (default: {defaults.steps})'
    )
    return group


def add_model_args(
    parser: argparse.ArgumentParser,
    multi: bool = False,
    required: bool = False
) -> argparse._ArgumentGroup:
    """Add model specification arguments.

    Args:
        parser: ArgumentParser to add arguments to
        multi: If True, accept multiple models (--models), otherwise single (--model)
        required: If True, make the argument required

    Returns:
        The argument group for chaining
    """
    group = parser.add_argument_group('Model Selection')

    if multi:
        group.add_argument(
            '--models', '-m',
            nargs='+',
            required=required,
            metavar='ENGINE:MODEL',
            help='Models to use (format: engine:model, e.g., pytorch:google/gemma-2-2b-it)'
        )
    else:
        group.add_argument(
            '--model', '-m',
            type=str,
            default=f'{cfg.DEFAULT_ENGINE}:{cfg.DEFAULT_MODEL_NAME}',
            metavar='ENGINE:MODEL',
            help=f'Model to use (format: engine:model, default: {cfg.DEFAULT_ENGINE}:{cfg.DEFAULT_MODEL_NAME})'
        )

    group.add_argument(
        '--engine', '-e',
        type=str,
        choices=list_engines(),
        help='Override engine type (usually inferred from model spec)'
    )

    return group


def add_verbosity_args(parser: argparse.ArgumentParser) -> argparse._ArgumentGroup:
    """Add verbosity control arguments.

    Args:
        parser: ArgumentParser to add arguments to

    Returns:
        The argument group for chaining
    """
    group = parser.add_argument_group('Output Control')
    group.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output and debugging information'
    )
    group.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress non-essential output'
    )
    return group


def add_mind_meld_args(parser: argparse.ArgumentParser) -> argparse._ArgumentGroup:
    """Add Mind Meld specific arguments.

    Args:
        parser: ArgumentParser to add arguments to

    Returns:
        The argument group for chaining
    """
    group = parser.add_argument_group('Mind Meld Options')
    group.add_argument(
        '--strategy',
        type=str,
        default='fixed',
        choices=['fixed', 'pattern', 'perplexity', 'round_robin', 'random'],
        help='Model swap strategy (default: fixed)'
    )
    group.add_argument(
        '--fixed-interval',
        type=int,
        default=3,
        metavar='INT',
        help='Tokens between swaps for fixed strategy (default: 3)'
    )
    group.add_argument(
        '--use-blending',
        action='store_true',
        help='Enable logit blending instead of swapping'
    )
    group.add_argument(
        '--use-weighted-average',
        action='store_true',
        help='Use entropy-weighted averaging of all models'
    )
    group.add_argument(
        '--use-abe',
        action='store_true',
        help='Use Agreement-Based Ensembling'
    )
    group.add_argument(
        '--prompt',
        type=str,
        metavar='TEXT',
        help='Initial prompt for generation'
    )
    return group


# ============================================================================
# Convenience Functions
# ============================================================================

def add_common_args(
    parser: argparse.ArgumentParser,
    include_sampling: bool = True,
    include_generation: bool = True,
    include_verbosity: bool = True
) -> None:
    """Add commonly used argument groups to a parser.

    Args:
        parser: ArgumentParser to add arguments to
        include_sampling: Include temperature/top-k/top-p
        include_generation: Include steps
        include_verbosity: Include verbose/quiet flags
    """
    if include_sampling:
        add_sampling_args(parser)
    if include_generation:
        add_generation_args(parser)
    if include_verbosity:
        add_verbosity_args(parser)


def normalize_args(args: argparse.Namespace) -> argparse.Namespace:
    """Normalize argument names for consistency.

    Converts hyphenated args to underscored versions used internally.
    E.g., args.top_k from --top-k

    Args:
        args: Parsed arguments namespace

    Returns:
        Same namespace with normalized attribute names
    """
    # Handle top-k -> top_k conversion (argparse does this automatically)
    # This function exists for any additional normalization needed
    return args
