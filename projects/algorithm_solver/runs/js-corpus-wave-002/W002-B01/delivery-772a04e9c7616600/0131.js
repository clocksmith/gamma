function partition(s) {
  const length = s.length;
  const palindrome = Array.from(
    { length },
    () => new Array(length).fill(false)
  );

  for (let start = length - 1; start >= 0; start -= 1) {
    for (let end = start; end < length; end += 1) {
      palindrome[start][end] =
        s[start] === s[end] &&
        (end - start <= 2 || palindrome[start + 1][end - 1]);
    }
  }

  const result = [];
  const current = [];

  function search(start) {
    if (start === length) {
      result.push(current.slice());
      return;
    }

    for (let end = start; end < length; end += 1) {
      if (!palindrome[start][end]) {
        continue;
      }

      current.push(s.slice(start, end + 1));
      search(end + 1);
      current.pop();
    }
  }

  search(0);
  return result;
}
