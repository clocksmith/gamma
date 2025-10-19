#!/usr/bin/env python3
"""
Auto-Fixer for GAMMA Feedback Loop
Suggests and applies fixes for common test failures.
"""

import re
import os
from typing import List, Dict, Optional, Any
from pathlib import Path
from log_analyzer import TestFailure


class AutoFixer:
    """Automatically suggests and applies fixes for common errors."""

    def __init__(self, auto_apply: bool = False):
        self.auto_apply = auto_apply
        self.applied_fixes = []

    def suggest_fixes(self, failure: TestFailure) -> List[Dict[str, Any]]:
        """
        Generate fix suggestions for a test failure.

        Returns a list of fix dictionaries with:
        - description: Human-readable description
        - type: Type of fix (import, assertion, etc.)
        - file_path: File to modify
        - fix_function: Function to apply the fix
        - confidence: low, medium, high
        """
        suggestions = []

        # Route to specific fix generators based on error type
        if 'import' in failure.error_type.lower():
            suggestions.extend(self._fix_import_error(failure))
        elif 'attribute' in failure.error_type.lower():
            suggestions.extend(self._fix_attribute_error(failure))
        elif 'assertion' in failure.error_type.lower():
            suggestions.extend(self._fix_assertion_error(failure))
        elif 'name' in failure.error_type.lower():
            suggestions.extend(self._fix_name_error(failure))
        elif 'type' in failure.error_type.lower():
            suggestions.extend(self._fix_type_error(failure))
        elif 'syntax' in failure.error_type.lower():
            suggestions.extend(self._fix_syntax_error(failure))

        return suggestions

    def _fix_import_error(self, failure: TestFailure) -> List[Dict[str, Any]]:
        """Fix import errors."""
        suggestions = []

        # Extract module name from error message
        module_match = re.search(r"No module named '([^']+)'", failure.error_message)
        if not module_match:
            module_match = re.search(r"cannot import name '([^']+)'", failure.error_message)

        if not module_match:
            return suggestions

        module_name = module_match.group(1)

        # Suggestion 1: Add to requirements.txt
        suggestions.append({
            'description': f"Add '{module_name}' to requirements.txt",
            'type': 'add_requirement',
            'file_path': 'requirements.txt',
            'module_name': module_name,
            'confidence': 'medium',
            'fix_data': {
                'module': module_name
            }
        })

        # Suggestion 2: Check if it's a local import issue
        if failure.file_path:
            suggestions.append({
                'description': f"Add sys.path.insert for local imports in {failure.file_path}",
                'type': 'fix_local_import',
                'file_path': failure.file_path,
                'confidence': 'low',
                'fix_data': {
                    'module': module_name,
                    'file': failure.file_path
                }
            })

        # Suggestion 3: Check if module exists but is in wrong location
        suggestions.append({
            'description': f"Search for '{module_name}' in codebase and fix import path",
            'type': 'fix_import_path',
            'file_path': failure.file_path,
            'confidence': 'high',
            'fix_data': {
                'module': module_name
            }
        })

        return suggestions

    def _fix_attribute_error(self, failure: TestFailure) -> List[Dict[str, Any]]:
        """Fix attribute errors."""
        suggestions = []

        # Extract attribute name
        attr_match = re.search(r"'(\w+)' object has no attribute '(\w+)'", failure.error_message)
        if attr_match:
            obj_type = attr_match.group(1)
            attr_name = attr_match.group(2)

            suggestions.append({
                'description': f"Add '{attr_name}' attribute to {obj_type} class",
                'type': 'add_attribute',
                'file_path': failure.file_path,
                'confidence': 'medium',
                'fix_data': {
                    'class': obj_type,
                    'attribute': attr_name
                }
            })

        return suggestions

    def _fix_assertion_error(self, failure: TestFailure) -> List[Dict[str, Any]]:
        """Fix assertion errors."""
        suggestions = []

        # Check if it's a simple equality assertion
        if '!=' in failure.error_message or '==' in failure.error_message:
            suggestions.append({
                'description': "Review test expectations - assertion mismatch detected",
                'type': 'review_assertion',
                'file_path': failure.file_path,
                'confidence': 'low',
                'fix_data': {
                    'message': failure.error_message,
                    'line': failure.line_number
                }
            })

        return suggestions

    def _fix_name_error(self, failure: TestFailure) -> List[Dict[str, Any]]:
        """Fix name errors (undefined variables)."""
        suggestions = []

        # Extract variable name
        name_match = re.search(r"name '(\w+)' is not defined", failure.error_message)
        if name_match:
            var_name = name_match.group(1)

            suggestions.append({
                'description': f"Define variable '{var_name}' before use",
                'type': 'define_variable',
                'file_path': failure.file_path,
                'confidence': 'medium',
                'fix_data': {
                    'variable': var_name,
                    'line': failure.line_number
                }
            })

        return suggestions

    def _fix_type_error(self, failure: TestFailure) -> List[Dict[str, Any]]:
        """Fix type errors."""
        suggestions = []

        suggestions.append({
            'description': "Review type compatibility in function call",
            'type': 'fix_type',
            'file_path': failure.file_path,
            'confidence': 'low',
            'fix_data': {
                'message': failure.error_message
            }
        })

        return suggestions

    def _fix_syntax_error(self, failure: TestFailure) -> List[Dict[str, Any]]:
        """Fix syntax errors."""
        suggestions = []

        suggestions.append({
            'description': f"Fix syntax error at {failure.file_path}:{failure.line_number}",
            'type': 'fix_syntax',
            'file_path': failure.file_path,
            'confidence': 'high',
            'fix_data': {
                'line': failure.line_number,
                'message': failure.error_message
            }
        })

        return suggestions

    def apply_fix(self, suggestion: Dict[str, Any]) -> bool:
        """
        Apply a suggested fix.

        Returns True if fix was applied successfully, False otherwise.
        """
        try:
            fix_type = suggestion['type']

            if fix_type == 'add_requirement':
                return self._apply_add_requirement(suggestion)
            elif fix_type == 'fix_local_import':
                return self._apply_fix_local_import(suggestion)
            elif fix_type == 'fix_import_path':
                return self._apply_fix_import_path(suggestion)
            elif fix_type == 'add_attribute':
                return self._apply_add_attribute(suggestion)
            else:
                # For other types, just log the suggestion
                print(f"Manual fix needed: {suggestion['description']}")
                return False

        except Exception as e:
            print(f"Error applying fix: {e}")
            return False

    def _apply_add_requirement(self, suggestion: Dict[str, Any]) -> bool:
        """Add a module to requirements.txt."""
        module = suggestion['fix_data']['module']
        req_file = Path(suggestion['file_path'])

        if not req_file.exists():
            print(f"Requirements file not found: {req_file}")
            return False

        # Check if already in requirements
        with open(req_file, 'r') as f:
            content = f.read()
            if module in content:
                print(f"Module '{module}' already in requirements")
                return False

        # Add to requirements
        with open(req_file, 'a') as f:
            f.write(f"\n{module}\n")

        print(f"Added '{module}' to {req_file}")
        self.applied_fixes.append(suggestion)
        return True

    def _apply_fix_local_import(self, suggestion: Dict[str, Any]) -> bool:
        """Fix local import by adding sys.path manipulation."""
        file_path = Path(suggestion['file_path'])

        if not file_path or not file_path.exists():
            return False

        # Read file
        with open(file_path, 'r') as f:
            lines = f.readlines()

        # Check if sys.path manipulation already exists
        has_sys_path = any('sys.path.insert' in line for line in lines)
        if has_sys_path:
            return False

        # Find first import
        first_import_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                first_import_idx = i
                break

        if first_import_idx is None:
            first_import_idx = 0

        # Insert sys.path manipulation
        sys_path_code = [
            "import sys\n",
            "import os\n",
            "sys.path.insert(0, os.path.dirname(os.path.abspath('.')))\n",
            "\n"
        ]

        lines = lines[:first_import_idx] + sys_path_code + lines[first_import_idx:]

        # Write back
        with open(file_path, 'w') as f:
            f.writelines(lines)

        print(f"Added sys.path manipulation to {file_path}")
        self.applied_fixes.append(suggestion)
        return True

    def _apply_fix_import_path(self, suggestion: Dict[str, Any]) -> bool:
        """Try to fix import path by searching for the module."""
        module_name = suggestion['fix_data']['module']

        # This is a manual fix - requires investigation
        print(f"Manual investigation needed: search codebase for '{module_name}'")
        print(f"  Suggested file: {suggestion['file_path']}")

        # Could implement automatic search and fix here
        # For now, just report
        return False

    def _apply_add_attribute(self, suggestion: Dict[str, Any]) -> bool:
        """Add missing attribute to a class."""
        # This requires class analysis - manual for now
        print(f"Manual fix needed: Add attribute '{suggestion['fix_data']['attribute']}' "
              f"to class '{suggestion['fix_data']['class']}'")
        return False

    def get_applied_fixes(self) -> List[Dict[str, Any]]:
        """Get list of all applied fixes."""
        return self.applied_fixes


def main():
    """Demo/testing of auto fixer."""
    from log_analyzer import TestFailure

    # Demo import error
    failure = TestFailure(
        test_name="test_example",
        error_type="Import Error",
        error_message="No module named 'numpy'",
        file_path="tests/test_example.py",
        line_number=5
    )

    fixer = AutoFixer()
    suggestions = fixer.suggest_fixes(failure)

    print(f"Suggestions for {failure.test_name}:\n")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. {suggestion['description']}")
        print(f"   Type: {suggestion['type']}")
        print(f"   Confidence: {suggestion['confidence']}")
        print()


if __name__ == '__main__':
    main()
