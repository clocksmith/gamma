// External ListNode shape: {val: number, next: ListNode | null}.
class Link {
  constructor(next_node = null) {
    this.next = next_node;
  }
}

function mergeRuns(left, right) {
  const sentinel = new Link();
  let tail = sentinel;
  while (left !== null && right !== null) {
    if (left.val <= right.val) {
      tail.next = left;
      left = left.next;
    } else {
      tail.next = right;
      right = right.next;
    }
    tail = tail.next;
  }
  tail.next = left !== null ? left : right;
  return sentinel.next;
}

class Solution {
  mergeKLists(lists) {
    let runs = lists.slice();
    while (runs.length > 1) {
      const next_runs = [];
      for (let index = 0; index < runs.length; index += 2) {
        const left = runs[index];
        const right = index + 1 < runs.length ? runs[index + 1] : null;
        next_runs.push(mergeRuns(left, right));
      }
      runs = next_runs;
    }
    return runs.length > 0 ? runs[0] : null;
  }
}
