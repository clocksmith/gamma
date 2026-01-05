"""
Functions for handling user input and interactive menus.
"""

from typing import List, Optional, Dict, Any
import argparse

from src.core import config as cfg
from src.ui import components as uic
from src.core.models.model_catalog import ModelSelector
from src.engines.capability_registry import list_engines_with, get_engine_info

SUPPORTED_ENGINES_UI_LIST = list_engines_with(supports_logits=True)

def get_user_input(
    prompt: str,
    valid_choices: Optional[List[str]] = None,
    allow_quit: bool = True,
    allow_empty: bool = False,
    default_val_on_empty: Optional[str] = None,
) -> str:
    """Gets and validates user input from the console."""
    while True:
        full_prompt_parts = [prompt]
        if valid_choices and not allow_empty:
            full_prompt_parts.append(f" ({'/'.join(valid_choices)})")
        if default_val_on_empty is not None and allow_empty:
            full_prompt_parts.append(f" [Enter for '{default_val_on_empty}']")
        full_prompt_parts.append(": ")
        full_prompt_str = "".join(full_prompt_parts)

        try:
            user_input = input(full_prompt_str).strip()
        except (EOFError, KeyboardInterrupt):
            print(uic.color_text("\nExiting game.", cfg.COLOR_YELLOW))
            exit(0)

        if allow_quit and user_input.lower() == cfg.SHORTCUT_QUIT:
            return cfg.SHORTCUT_QUIT
        if allow_empty and not user_input:
            return default_val_on_empty if default_val_on_empty is not None else ""

        user_input_lower = user_input.lower()
        if valid_choices:
            valid_choices_lower = [choice.lower() for choice in valid_choices]
            if user_input_lower in valid_choices_lower:
                return valid_choices[valid_choices_lower.index(user_input_lower)]
            else:
                print(uic.color_text(f"Invalid choice. Please choose from: {', '.join(valid_choices)}", cfg.COLOR_RED))
        elif user_input:
            return user_input
        elif not allow_empty:
            print(uic.color_text("Input cannot be empty.", cfg.COLOR_RED))

def confirm_or_modify_config(args: argparse.Namespace) -> bool:
    """Allows the user to confirm or modify the game configuration."""
    # This function is highly coupled with the main script's argument parsing.
    # For now, we'll keep it here, but a more robust solution would be to
    # create a dedicated configuration object.
    from src.ui.displays import display_current_config # Avoid circular import

    param_details_core = {
        "e": ("engine", "Engine", lambda current_val: select_engine_interactively(current_val), f"from {SUPPORTED_ENGINES_UI_LIST}"),
        "m": ("model", "Model Identifier", lambda current_val, eng=args.engine: select_model_interactively(eng, current_val), "name/path"),
        "s": ("steps", "Max Rounds", lambda v: int(v), "integer"),
        "t": ("temperature", "Temperature", lambda v: float(v), "float (e.g. 0.7)"),
        "k": ("top_k", "Top-K", lambda v: int(v), "integer (e.g. 8)"),
        "p": ("top_p", "Top-P", lambda v: float(v), "float (e.g. 0.95)"),
        "c": ("num_choices", "Choices/Round", lambda v: int(v), "integer"),
        "len": ("permutation_length", "Tokens/Choice", lambda v: int(v), "integer"),
        "fw": ("focus_words", "Focus Words Mode", lambda v: v.lower() in ["true", "yes", "y", "1"], "yes/no"),
        "pc": ("player_choice_mode", "Player Choice Mode", lambda v: v.lower() in ["true", "yes", "y", "1"], "yes/no"),
        "att": ("show_attention", "Show Attention", lambda v: v.lower() in ["true", "yes", "y", "1"], "yes/no"),
        "vrb": ("verbose", "Verbose Mode", lambda v: v.lower() in ["true", "yes", "y", "1"], "yes/no"),
    }
    while True:
        display_current_config(args, title="Confirm Game Configuration")
        choice = get_user_input(
            f"Accept this configuration and start? ({cfg.SHORTCUT_CONFIRM_CONFIG_ACCEPT}=yes, {cfg.SHORTCUT_CONFIRM_CONFIG_MODIFY}=modify)",
            [cfg.SHORTCUT_CONFIRM_CONFIG_ACCEPT.lower(), cfg.SHORTCUT_CONFIRM_CONFIG_MODIFY.lower()],
            allow_quit=True,
            allow_empty=True,
            default_val_on_empty=cfg.SHORTCUT_CONFIRM_CONFIG_ACCEPT.lower()
        ).lower()

        if choice == cfg.SHORTCUT_QUIT:
            return False
        if choice == cfg.SHORTCUT_CONFIRM_CONFIG_ACCEPT:
            return True
        if choice == cfg.SHORTCUT_CONFIRM_CONFIG_MODIFY:
            uic.print_header("Modify Configuration")
            print("Enter key of parameter to change (e.g., 't' for Temperature), then new value. Press Enter to skip.")
            all_modifiable_params = dict(param_details_core)

            for key, (attr, desc, _, type_h) in all_modifiable_params.items():
                current_val = getattr(args, attr, "Not Set")
                current_val_disp = "Yes" if isinstance(current_val, bool) else f"{current_val:.2f}" if isinstance(current_val, float) else str(current_val)
                prompt_text = f"  ({key}) {desc:<25} (current: {current_val_disp}"
                if type_h:
                    prompt_text += f", expects {type_h}"
                prompt_text += "): "
                new_val_str = get_user_input(prompt_text, allow_quit=False, allow_empty=True, default_val_on_empty=cfg.SHORTCUT_MODIFY_PARAM_SKIP)
                if new_val_str == cfg.SHORTCUT_MODIFY_PARAM_SKIP:
                    continue
                try:
                    convert_func = all_modifiable_params[key][2]
                    new_val = convert_func(new_val_str)
                    if new_val is not None:
                        setattr(args, attr, new_val)
                except (ValueError, TypeError) as e:
                    print(uic.color_text(f"Invalid value for '{desc}': {e}", cfg.COLOR_RED))
    return False

def select_engine_interactively(current_default_engine: str) -> Optional[str]:
    """Allows the user to select a game engine interactively."""
    uic.print_header("Engine Selection")
    print("Choose the backend engine:")
    for i, name in enumerate(SUPPORTED_ENGINES_UI_LIST):
        info = get_engine_info(name)
        label = info.display_name if info else name
        suffix = "*" if name == current_default_engine else ""
        print(f"  {i+1}) {label} ({name}){suffix}")
    prompt = f"Select engine number (1-{len(SUPPORTED_ENGINES_UI_LIST)})"
    default_idx_str = str(SUPPORTED_ENGINES_UI_LIST.index(current_default_engine) + 1) if current_default_engine in SUPPORTED_ENGINES_UI_LIST else "1"
    choice = get_user_input(prompt, [str(i + 1) for i in range(len(SUPPORTED_ENGINES_UI_LIST))], allow_empty=True, default_val_on_empty=default_idx_str)
    if choice == cfg.SHORTCUT_QUIT:
        return None
    return SUPPORTED_ENGINES_UI_LIST[int(choice) - 1]

def select_model_interactively(selected_engine: str, current_default_model: Optional[str] = None) -> Optional[str]:
    """Allows the user to select a model interactively."""
    uic.print_header(f"Model Selection ({selected_engine.capitalize()} Engine)")
    selector = ModelSelector(selected_engine)
    return selector.select_model()
