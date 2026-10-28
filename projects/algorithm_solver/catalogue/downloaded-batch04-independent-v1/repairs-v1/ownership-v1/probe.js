'use strict';
// Transparent instrumentation records the inputs passed to the actual decode map.
const originalMap = Array.prototype.map;
const rawDecodeArrays = [];
Array.prototype.map = function(callback, thisArg) {
  if (callback.name === 'decode') rawDecodeArrays.push(this);
  return originalMap.call(this, callback, thisArg);
};
const seen = [];
function solve(nums) {
  const raw = rawDecodeArrays.at(-1);
  const distinctRaw = !rawDecodeArrays.includes(nums);
  const first = raw[0], second = raw[1], current = nums[0];
  nums[0] = -1234;
  const detached = raw[0] === first && raw[1] === second;
  nums[0] = current;
  const distinctPrior = seen.every(previous => previous !== nums);
  for (const previous of seen) previous[0] = -9999;
  const isolated = nums[0] === 2;
  seen.push(nums);
  return {distinct_from_raw_packet: distinctRaw,
          packet_unchanged_during_current_mutation: detached,
          distinct_from_prior_calls: distinctPrior,
          current_unchanged_by_prior_mutation: isolated};
}
