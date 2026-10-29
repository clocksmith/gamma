"use strict";

function maxSubseq(arr, t) {
  if (t === 0) return [];
  let drop = arr.length - t;
  const stack = [];
  for (let i = 0; i < arr.length; i++) {
    const d = arr[i];
    while (drop > 0 && stack.length > 0 && stack[stack.length - 1] < d) {
      stack.pop();
      drop--;
    }
    stack.push(d);
  }
  return stack.slice(0, t);
}

function greaterSuffix(a, i, b, j) {
  const m = a.length, n = b.length;
  while (i < m && j < n && a[i] === b[j]) {
    i++;
    j++;
  }
  if (j === n) return true;
  if (i === m) return false;
  return a[i] > b[j];
}

function lexGreater(a, b) {
  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) return a[i] > b[i];
  }
  return false;
}

function solve(nums1, nums2, k) {
  const m = nums1.length, n = nums2.length;
  const start = Math.max(0, k - n);
  const end = Math.min(k, m);
  let best = null;
  for (let s1 = start; s1 <= end; s1++) {
    const a = maxSubseq(nums1, s1);
    const b = maxSubseq(nums2, k - s1);
    const merged = new Array(k);
    let i = 0, j = 0;
    for (let idx = 0; idx < k; idx++) {
      if (greaterSuffix(a, i, b, j)) {
        merged[idx] = a[i++];
      } else {
        merged[idx] = b[j++];
      }
    }
    if (best === null || lexGreater(merged, best)) {
      best = merged;
    }
  }
  return best;
}

function maxNumber(nums1, nums2, k) {
  return solve(nums1, nums2, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.maxNumber = maxNumber;
