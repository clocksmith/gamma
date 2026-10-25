class Solution {
  distributeCandies(candies, num_people) {
    const result = Array(num_people).fill(0);
    let remaining = candies;
    let gift = 1;
    let person = 0;
    while (remaining > 0) {
      const amount = Math.min(gift, remaining);
      result[person] += amount;
      remaining -= amount;
      gift += 1;
      person = (person + 1) % num_people;
    }
    return result;
  }
}
