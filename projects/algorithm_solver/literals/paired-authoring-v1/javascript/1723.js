function canAssign(jobs, workers, limit) {
  const loads = Array(workers).fill(0);

  function place(index) {
    if (index === jobs.length) {
      return true;
    }
    const seen = new Set();
    for (let worker = 0; worker < workers; worker += 1) {
      const previous = loads[worker];
      if (seen.has(previous)) {
        continue;
      }
      seen.add(previous);
      if (previous + jobs[index] <= limit) {
        loads[worker] += jobs[index];
        const possible = place(index + 1);
        loads[worker] -= jobs[index];
        if (possible) {
          return true;
        }
      }
      if (previous === 0) {
        break;
      }
    }
    return false;
  }

  return place(0);
}


class Solution {
  minimumTimeRequired(jobs, k) {
    const ordered = jobs.slice().sort((first, second) => second - first);
    let left = ordered[0];
    let right = 0;
    for (const job of ordered) {
      right += job;
    }
    while (left < right) {
      const middle = left + Math.floor((right - left) / 2);
      if (canAssign(ordered, k, middle)) {
        right = middle;
      } else {
        left = middle + 1;
      }
    }
    return left;
  }
}
