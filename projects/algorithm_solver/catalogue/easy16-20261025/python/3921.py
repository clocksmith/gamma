def solve(events: list[str]) -> list[int]:
    """Accumulate events until the tenth wicket. O(n) time, O(1) space."""
    score = 0
    counter = 0
    for event in events:
        if event == "W":
            counter += 1
            if counter == 10:
                break
        elif event == "WD" or event == "NB":
            score += 1
        else:
            score += int(event)
    return [score, counter]
