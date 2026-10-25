function solve(matrix) {
  // O(n^2) time, O(n) output space; no input mutation.
  const answer = [];
  for (const row of matrix) {
    let degree = 0;
    for (const edge of row) degree += edge;
    answer.push(degree);
  }
  return answer;
}
