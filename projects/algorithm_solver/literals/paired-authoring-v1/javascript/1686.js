class Solution {
  stoneGameVI(aliceValues, bobValues) {
    const order = Array.from({length: aliceValues.length}, (_, index) => index);
    order.sort((first, second) => {
      const combined = aliceValues[second] + bobValues[second] - aliceValues[first] - bobValues[first];
      return combined !== 0 ? combined : first - second;
    });
    let difference = 0;
    for (let turn = 0; turn < order.length; turn += 1) {
      const index = order[turn];
      if (turn % 2 === 0) {
        difference += aliceValues[index];
      } else {
        difference -= bobValues[index];
      }
    }
    if (difference > 0) {
      return 1;
    }
    if (difference < 0) {
      return -1;
    }
    return 0;
  }
}
