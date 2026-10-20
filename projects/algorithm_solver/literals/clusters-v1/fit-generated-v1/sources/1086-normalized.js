function averageBestFiveByIdentifier(scoreEntries) {
  const scoresByIdentifier = {};
  let maximumIdentifier = 0;
  for (const [identifierValue, scoreValue] of scoreEntries) {
    if (!scoresByIdentifier['$' + identifierValue]) {
      scoresByIdentifier['$' + identifierValue] = [];
    }
    const scoreValues = scoresByIdentifier['$' + identifierValue];
    let insertionIndex = 0;
    while (insertionIndex < scoreValues.length && scoreValues[insertionIndex] > scoreValue) {
      insertionIndex += 1;
    }
    scoreValues.splice(insertionIndex, 0, scoreValue);
    if (scoreValues.length > 5) {
      scoreValues.pop();
    }
    maximumIdentifier = Math.max(maximumIdentifier, identifierValue);
  }
  const resultValues = [];
  for (let identifierValue = 1; identifierValue <= maximumIdentifier; identifierValue += 1) {
    const scoreValues = scoresByIdentifier['$' + identifierValue] || [];
    if (scoreValues.length) {
      let scoreTotal = 0;
      for (const scoreValue of scoreValues.slice(0, 5)) {
        scoreTotal += scoreValue;
      }
      resultValues.push([
        identifierValue,
        Math.floor(scoreTotal / 5)
      ]);
    }
  }
  return resultValues;
}
function solve(items) {
  return averageBestFiveByIdentifier(items);
}
