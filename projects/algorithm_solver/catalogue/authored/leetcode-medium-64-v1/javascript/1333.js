'use strict';

// 1333. Filter Restaurants by Vegan-Friendly, Price and Distance: filter eligible records then sort by descending rating and identifier.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(restaurants, veganFriendly, maxPrice, maxDistance) {
  const eligible = restaurants.filter(row => (!veganFriendly || row[2] === 1)
    && row[3] <= maxPrice && row[4] <= maxDistance);
  eligible.sort((left, right) => right[1] - left[1] || right[0] - left[0]);
  return eligible.map(row => row[0]);
}

const filterRestaurants = solve;
class Solution {
  filterRestaurants(restaurants, veganFriendly, maxPrice, maxDistance) { return solve(restaurants, veganFriendly, maxPrice, maxDistance); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, filterRestaurants };
