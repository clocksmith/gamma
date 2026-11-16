"""Find references to a symbol."""

import subprocess


def execute(symbol: str, path: str = ".") -> dict:
    """
    Find all references to a symbol (function, class, variable).

    Args:
        symbol: Symbol name to find
        path: Directory to search

    Returns:
        dict with definitions and usages
    """
    try:
        # Find definitions (def, class, =)
        def_patterns = [
            f"def {symbol}",
            f"class {symbol}",
            f"{symbol} =",
            f"{symbol}:",  # dict key, type annotation
        ]

        definitions = []
        usages = []

        for pattern in def_patterns:
            result = subprocess.run(
                ["grep", "-rn", "--include=*.py", pattern, path],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.stdout:
                definitions.extend(result.stdout.strip().split("\n"))

        # Find all usages
        result = subprocess.run(
            ["grep", "-rn", "--include=*.py", f"\\b{symbol}\\b", path],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.stdout:
            usages = result.stdout.strip().split("\n")

        # Dedupe
        definitions = list(set(definitions))[:20]
        usages = list(set(usages) - set(definitions))[:50]

        return {
            "definitions": definitions,
            "usages": usages,
            "total_refs": len(definitions) + len(usages),
        }
    except subprocess.TimeoutExpired:
        return {"error": "Search timed out", "definitions": [], "usages": []}
    except Exception as e:
        return {"error": str(e), "definitions": [], "usages": []}


execute.tool_info = {
    "tags": ["search", "references", "symbol", "code"],
}
