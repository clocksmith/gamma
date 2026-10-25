class Solution {
  maxProduct(nums) {
    let largest = 0;
    let second = 0;
    for (const value of nums) {
      if (value >= largest) {
        second = largest;
        largest = value;
      } else if (value > second) {
        second = value;
      }
    }
    return (largest - 1) * (second - 1);
  }
}
