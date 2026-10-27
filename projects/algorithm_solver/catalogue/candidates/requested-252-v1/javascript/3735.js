/**
 * 3735. Lexicographically Smallest String After Reverse II
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(s).
 * Algorithm: Exact suffix array, Kasai LCP, and range-minimum queries compare every prefix/suffix reversal as at most two source fragments.
 * Complexity: O(n log n) time; O(n) space. No quadratic string construction and no probabilistic hash equality.
 * Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
 * Mutation: Does not mutate input arrays, rows, strings, or trees.
 * Interface: Canonical solve(s). Native judge method name was not supplied or independently verified.
 * Specification: https://leetcode.com/problems/lexicographically-smallest-string-after-reverse-ii/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3735.Lexicographically%20Smallest%20String%20After%20Reverse%20II/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 * Contract note: The original string is reachable by the required length-one reversal. The final answer is constructed once; separators are outside the input alphabet.
 */

function solve(s) {
  const length = s.length;
  const text = s + "{" + s.split("").reverse().join("") + "$";
  const size = text.length;
  let counts = new Int32Array(128);
  for (let index = 0; index < size; index += 1) counts[text.charCodeAt(index)] += 1;
  for (let index = 1; index < counts.length; index += 1) counts[index] += counts[index - 1];
  let suffixes = new Int32Array(size);
  for (let index = size - 1; index >= 0; index -= 1) {
    const code = text.charCodeAt(index);
    counts[code] -= 1;
    suffixes[counts[code]] = index;
  }
  let ranks = new Int32Array(size);
  let classes = 1;
  for (let index = 1; index < size; index += 1) {
    if (text[suffixes[index]] !== text[suffixes[index - 1]]) classes += 1;
    ranks[suffixes[index]] = classes - 1;
  }
  for (let width = 1; width < size && classes < size; width *= 2) {
    const shifted = new Int32Array(size);
    counts = new Int32Array(classes);
    for (let offset = 0; offset < size; offset += 1) {
      let index = suffixes[offset] - width;
      if (index < 0) index += size;
      shifted[offset] = index;
      counts[ranks[index]] += 1;
    }
    for (let index = 1; index < classes; index += 1) counts[index] += counts[index - 1];
    const ordered = new Int32Array(size);
    for (let offset = size - 1; offset >= 0; offset -= 1) {
      const index = shifted[offset];
      const rank = ranks[index];
      counts[rank] -= 1;
      ordered[counts[rank]] = index;
    }
    const newRanks = new Int32Array(size);
    let newClasses = 1;
    for (let offset = 1; offset < size; offset += 1) {
      const current = ordered[offset];
      const previous = ordered[offset - 1];
      if (ranks[current] !== ranks[previous] || ranks[(current + width) % size] !== ranks[(previous + width) % size]) newClasses += 1;
      newRanks[current] = newClasses - 1;
    }
    suffixes = ordered;
    ranks = newRanks;
    classes = newClasses;
  }
  const common = new Int32Array(size);
  let shared = 0;
  for (let index = 0; index < size; index += 1) {
    const rank = ranks[index];
    if (rank === 0) {
      shared = 0;
      continue;
    }
    const previous = suffixes[rank - 1];
    while (index + shared < size && previous + shared < size && text[index + shared] === text[previous + shared]) shared += 1;
    common[rank] = shared;
    if (shared > 0) shared -= 1;
  }
  let base = 1;
  while (base < size) base *= 2;
  const minimums = new Int32Array(2 * base).fill(size);
  minimums.set(common, base);
  for (let index = base - 1; index > 0; index -= 1) minimums[index] = Math.min(minimums[2 * index], minimums[2 * index + 1]);
  function longestCommon(first, second) {
    if (first === second) return size - first;
    let left = Math.min(ranks[first], ranks[second]) + 1 + base;
    let right = Math.max(ranks[first], ranks[second]) + 1 + base;
    let answer = size;
    while (left < right) {
      if (left % 2 === 1) answer = Math.min(answer, minimums[left++]);
      if (right % 2 === 1) answer = Math.min(answer, minimums[--right]);
      left = Math.floor(left / 2);
      right = Math.floor(right / 2);
    }
    return answer;
  }
  function isSmaller(candidate, incumbent) {
    let firstPart = 0;
    let secondPart = 0;
    let firstOffset = 0;
    let secondOffset = 0;
    while (firstPart < candidate.length && secondPart < incumbent.length) {
      const [firstStart, firstLength] = candidate[firstPart];
      const [secondStart, secondLength] = incumbent[secondPart];
      const available = Math.min(firstLength - firstOffset, secondLength - secondOffset);
      const same = Math.min(available, longestCommon(firstStart + firstOffset, secondStart + secondOffset));
      if (same < available) return text[firstStart + firstOffset + same] < text[secondStart + secondOffset + same];
      firstOffset += same;
      secondOffset += same;
      if (firstOffset === firstLength) {
        firstPart += 1;
        firstOffset = 0;
      }
      if (secondOffset === secondLength) {
        secondPart += 1;
        secondOffset = 0;
      }
    }
    return false;
  }
  const reverseStart = length + 1;
  let best = [[0, length]];
  for (let count = 1; count <= length; count += 1) {
    const prefix = [[reverseStart + length - count, count]];
    if (count < length) prefix.push([count, length - count]);
    if (isSmaller(prefix, best)) best = prefix;
    const suffix = [];
    if (count < length) suffix.push([0, length - count]);
    suffix.push([reverseStart, count]);
    if (isSmaller(suffix, best)) best = suffix;
  }
  return best.map(([start, count]) => text.slice(start, start + count)).join("");
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve };
}
