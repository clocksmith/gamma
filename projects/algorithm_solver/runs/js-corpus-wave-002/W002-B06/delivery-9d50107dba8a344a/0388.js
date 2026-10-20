function lengthLongestPath(input) {
  if (input.length === 0) return 0;
  const directoryLengths = [];
  let longest = 0;

  for (const line of input.split('\n')) {
    let depth = 0;
    while (depth < line.length && line[depth] === '\t') depth++;
    const name = line.slice(depth);
    const pathLength = (depth === 0 ? 0 : directoryLengths[depth - 1]) + name.length;
    if (name.includes('.')) {
      longest = Math.max(longest, pathLength);
    } else {
      directoryLengths[depth] = pathLength + 1;
    }
  }
  return longest;
}
