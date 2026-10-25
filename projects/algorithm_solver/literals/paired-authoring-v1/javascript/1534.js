class Solution {
  countGoodTriplets(arr, a, b, c) {
    let count = 0;
    for (let first = 0; first < arr.length; first += 1) {
      for (let second = first + 1; second < arr.length; second += 1) {
        if (Math.abs(arr[first] - arr[second]) > a) {
          continue;
        }
        for (let third = second + 1; third < arr.length; third += 1) {
          if (Math.abs(arr[second] - arr[third]) <= b && Math.abs(arr[first] - arr[third]) <= c) {
            count += 1;
          }
        }
      }
    }
    return count;
  }
}
