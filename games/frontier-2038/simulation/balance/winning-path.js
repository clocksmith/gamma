export const WINNING_PATH_CLASSIFIER = Object.freeze({
  id: "lane-margin-v1",
  hybridMargin: 1
});

const LANE_ORDER = [
  "research",
  "infrastructure",
  "adoption",
  "legitimacy",
  "capital",
  "mobility"
];

export function winningLaneScores(entry) {
  const actions = entry.actions || entry.metrics?.actions || {};
  return {
    research: (actions.research || 0) + (entry.capability || 0) / 3,
    infrastructure: (actions.build || 0) + (entry.facilities || 0),
    adoption: (actions.deploy || 0) + (entry.customers || 0),
    legitimacy: (actions.influence || 0) + (entry.trust || 0) / 2,
    capital: actions.fund || 0,
    mobility: actions.organize || 0
  };
}

export function winningPathMargin(entry) {
  const ranked = Object.entries(winningLaneScores(entry))
    .sort((left, right) =>
      right[1] - left[1] ||
      LANE_ORDER.indexOf(left[0]) - LANE_ORDER.indexOf(right[0])
    );
  return {
    primary: ranked[0][0],
    secondary: ranked[1][0],
    primaryScore: ranked[0][1],
    secondaryScore: ranked[1][1],
    gap: ranked[0][1] - ranked[1][1]
  };
}

export function classifyWinningPath(
  entry,
  { hybridMargin = WINNING_PATH_CLASSIFIER.hybridMargin } = {}
) {
  if (entry.agiDeclared) return "agi_declaration";
  const margin = winningPathMargin(entry);
  if (margin.gap > hybridMargin) return margin.primary;
  const lanes = [margin.primary, margin.secondary]
    .sort((left, right) => LANE_ORDER.indexOf(left) - LANE_ORDER.indexOf(right));
  return `${lanes[0]}_${lanes[1]}_hybrid`;
}
