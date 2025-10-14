# Project Style Guide

A consistent style is crucial for creating clean, maintainable, and high-quality artifacts. This guide defines the standards for all code in this project.

## Python

*   **Formatting:** All Python code MUST be formatted using `black`.
    ```bash
    # From within the virtual environment
    pip install black
    black .
    ```
*   **Docstrings:** All modules, functions, and methods MUST have a [Pydoc](https://www.python.org/dev/peps/pep-0257/)-style docstring. The docstring should explain the purpose, arguments, and return value.
    ```python
    def my_function(param1: int, param2: str) -> bool:
        """Explain what this function does.

        Args:
            param1: Describe the first parameter.
            param2: Describe the second parameter.

        Returns:
            Describe the return value.
        """
        # function body
        return True
    ```
*   **Type Hinting:** All function signatures MUST include type hints.
*   **Method Length:** Methods and functions should be short and focused on a single task. Aim for under 30 lines of code per function where feasible.
*   **Comments:** **No inline comments.** Code should be self-documenting. If a complex piece of logic needs explanation, it should either be broken down into simpler, well-named functions, or documented in the function's docstring.
*   **Imports:** Imports should be organized at the top of the file, grouped into three sections: standard library, third-party libraries, and local application imports.

## JavaScript

*   **Docstrings:** All functions MUST have a [JSDoc](https://jsdoc.app/)-style docstring.
    ```javascript
    /**
     * Explain what this function does.
     * @param {string} prompt - The user's input prompt.
     * @returns {Promise<Object>} A promise that resolves with the API response.
     */
    async function callGenerateApi(prompt) {
      // ... function body
    }
    ```
*   **Variables:** Use `const` by default. Use `let` only for variables that must be reassigned. Avoid `var`.
*   **Strict Mode:** All scripts should begin with `"use strict";`.
*   **Formatting:** Use a consistent formatting style (e.g., Prettier with default settings).

## HTML & CSS

*   **Semantics:** Use semantic HTML5 tags where appropriate (`<main>`, `<section>`, `<header>`, etc.).
*   **Accessibility:** Include `alt` tags for images and use ARIA roles where necessary.
*   **CSS Naming:** Use a consistent naming convention, such as BEM (Block, Element, Modifier), to keep CSS readable and scoped.
*   **Formatting:** Maintain a clean and readable format for both HTML and CSS.