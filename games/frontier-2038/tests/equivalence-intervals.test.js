import test from "node:test";
import assert from "node:assert/strict";

import {
  intervalFits,
  normalMeanInterval98,
  subsetMinusGrandMeanInterval98,
  wilsonInterval98,
} from "../lab/statistics/equivalence-intervals.js";

test("98% mean interval is exact for a constant sample", () => {
  assert.deepEqual(normalMeanInterval98([4, 4, 4]), {
    n: 3,
    estimate: 4,
    lower: 4,
    upper: 4,
    halfWidth: 0,
  });
});

test("subset contrast estimates subset minus the full-sample mean", () => {
  const interval = subsetMinusGrandMeanInterval98(
    [1, 3, 5, 7],
    [true, true, false, false],
  );
  assert.equal(interval.estimate, -2);
  assert.equal(interval.groupN, 2);
  assert.equal(interval.complementN, 2);
});

test("98% Wilson interval remains bounded and supports equivalence checks", () => {
  const interval = wilsonInterval98(90, 100);
  assert.equal(interval.estimate, 0.9);
  assert.ok(interval.lower > 0.79);
  assert.ok(interval.upper < 0.96);
  assert.equal(intervalFits(interval, 0.75, 1), true);
  assert.equal(intervalFits(interval, 0.85, 1), false);
});

