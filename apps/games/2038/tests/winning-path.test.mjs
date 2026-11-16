import assert from "node:assert/strict";
import test from "node:test";
import {
  classifyWinningPath,
  WINNING_PATH_CLASSIFIER,
  winningPathMargin
} from "../lab/balance/winning-path.js";

const standing = (overrides = {}) => ({
  actions: {
    fund: 1,
    research: 3,
    build: 2,
    organize: 0,
    deploy: 3,
    influence: 1
  },
  capability: 9,
  facilities: 2,
  customers: 4,
  trust: 4,
  agiDeclared: false,
  ...overrides
});

test("winning-path classifier recognizes a stable one-point hybrid margin", () => {
  assert.deepEqual(WINNING_PATH_CLASSIFIER, {
    id: "lane-margin-v1",
    hybridMargin: 1
  });
  const entry = standing();
  assert.deepEqual(winningPathMargin(entry), {
    primary: "adoption",
    secondary: "research",
    primaryScore: 7,
    secondaryScore: 6,
    gap: 1
  });
  assert.equal(
    classifyWinningPath(entry),
    "research_adoption_hybrid"
  );
  assert.equal(
    classifyWinningPath(entry, { hybridMargin: 0 }),
    "adoption"
  );
});

test("winning-path classifier keeps clear leaders and AGI declarations distinct", () => {
  assert.equal(
    classifyWinningPath(standing({ customers: 5, capability: 6 })),
    "adoption"
  );
  assert.equal(
    classifyWinningPath(standing({ agiDeclared: true })),
    "agi_declaration"
  );
});
