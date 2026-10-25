class Solution {
  findTheWinner(n, k) {
    let winner = 0;
    for (let size = 2; size <= n; size += 1) {
      winner = (winner + k) % size;
    }
    return winner + 1;
  }
}
