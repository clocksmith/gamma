def solve(windows, queries):
    seen = set()
    result = []
    # Last activation wins; untouched windows retain their relative order.
    for window in reversed(queries):
        if window not in seen:
            seen.add(window)
            result.append(window)
    result.extend(window for window in windows if window not in seen)
    return result
