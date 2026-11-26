let inputString = "";
let currentLine = 0;
process.stdin.on("data", (data) => {
  inputString += data;
});
process.stdin.on("end", function () {
  inputString = inputString
    .trim()
    .split("\n")
    .map((str) => str.trim());
  main();
});
function readLine() {
  return inputString[currentLine++];
}
function main() {
  let [totalPeople, t] = readLine()
    .split(" ")
    .map((n) => parseInt(n));
  const graph = {};
  const seenCouple = {};
  while (t--) {
    let [p1, p2] = readLine()
      .split(" ")
      .map((n) => parseInt(n));

    if (!seenCouple[`${p1}-${p2}`]) {
      seenCouple[`${p1}-${p2}`] = true;

      if (!graph[p1]) graph[p1] = { [p2]: true };
      else graph[p1][p2] = true;
      if (!graph[p2]) graph[p2] = { [p1]: true };
      else graph[p2][p1] = true;
    }
  }

  let max = 1;
  let visited = {};
  for (let key in graph) {
    if (!visited[key]) {
      const stack = [key];
      let count = 0;
      while (stack.length) {
        const node = stack.pop();
        visited[node] = true;
        count++;
        for (let key in graph[node]) {
          if (!visited[key]) {
            visited[key] = true;
            stack.push(key);
          }
        }
      }
      max = Math.max(max, count);
    }
  }
  console.log(max);
}
