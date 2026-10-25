class Solution {
  maxBottlesDrunk(numBottles, numExchange) {
    let empty = numBottles;
    let drunk = numBottles;
    let required = numExchange;
    while (empty >= required) {
      empty -= required;
      required += 1;
      empty += 1;
      drunk += 1;
    }
    return drunk;
  }
}
