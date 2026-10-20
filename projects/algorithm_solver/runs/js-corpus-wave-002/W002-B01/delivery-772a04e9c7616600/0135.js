function candy(ratings) {
  const length = ratings.length;
  const candies = new Array(length).fill(1);

  for (let index = 1; index < length; index += 1) {
    if (ratings[index] > ratings[index - 1]) {
      candies[index] = candies[index - 1] + 1;
    }
  }

  for (let index = length - 2; index >= 0; index -= 1) {
    if (ratings[index] > ratings[index + 1]) {
      candies[index] = Math.max(candies[index], candies[index + 1] + 1);
    }
  }

  return candies.reduce((total, value) => total + value, 0);
}
