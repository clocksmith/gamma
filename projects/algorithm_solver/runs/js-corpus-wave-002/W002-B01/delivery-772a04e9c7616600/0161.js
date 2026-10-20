function isOneEditDistance(s, t) {
  let shorter = s;
  let longer = t;

  if (shorter.length > longer.length) {
    [shorter, longer] = [longer, shorter];
  }

  if (longer.length - shorter.length > 1) {
    return false;
  }

  let shorterIndex = 0;
  let longerIndex = 0;
  let edits = 0;

  while (
    shorterIndex < shorter.length &&
    longerIndex < longer.length
  ) {
    if (shorter[shorterIndex] === longer[longerIndex]) {
      shorterIndex += 1;
      longerIndex += 1;
      continue;
    }

    edits += 1;
    if (edits > 1) {
      return false;
    }

    if (shorter.length === longer.length) {
      shorterIndex += 1;
    }
    longerIndex += 1;
  }

  if (
    shorterIndex < shorter.length ||
    longerIndex < longer.length
  ) {
    edits += 1;
  }

  return edits === 1;
}
