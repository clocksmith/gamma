function solve(n, requests) {
  // O(m) time and O(1) space; n bounds the request floors.
  let floor = 0;
  let answer = 0;
  for (const destination of requests) {
    answer += Math.abs(destination - floor);
    floor = destination;
  }
  return answer;
}
