'use strict';

// 2284. Sender With Largest Word Count: aggregate words per sender and break equal totals by the larger name.
// O(L + n A) time and O(n) auxiliary entries for L text characters and maximum name length A; inputs are read-only.
function solve(messages, senders) {
  const totals = new Map();
  for (let index = 0; index < messages.length; index += 1) {
    let words = 1;
    for (const character of messages[index]) if (character === ' ') words += 1;
    const sender = senders[index];
    totals.set(sender, (totals.get(sender) || 0) + words);
  }
  let bestName = '';
  let bestCount = -1;
  for (const [sender, count] of totals) {
    if (count > bestCount || (count === bestCount && sender > bestName)) {
      bestName = sender;
      bestCount = count;
    }
  }
  return bestName;
}

const largestWordCount = solve;
class Solution {
  largestWordCount(messages, senders) { return solve(messages, senders); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestWordCount };
