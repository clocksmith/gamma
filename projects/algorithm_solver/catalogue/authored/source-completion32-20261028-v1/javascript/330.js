// 330 — Patching Array. Original implementation; authored candidate, not independently qualified.
function solve(nums, n) {
  // Every value in [1, missing) is representable.
  let missing = 1, i = 0, patches = 0;
  while (missing <= n) {
    if (i < nums.length && nums[i] <= missing) missing += nums[i++];
    else { missing *= 2; patches++; }
  }
  return patches;
}

module.exports = { solve, minPatches: solve };
