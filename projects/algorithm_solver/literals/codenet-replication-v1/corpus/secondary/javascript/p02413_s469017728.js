process.stdin.resume();
process.stdin.setEncoding("utf8");

const reader = require("readline").createInterface({
  input: process.stdin,
  output: process.stdout,
});

const lines = [];

reader.on("line", (line) => {
  lines.push(line);
});

reader.on("close", () => {
  const [r, c] = parseLine(lines[0]);
  const sumRow = Array(c + 1).fill(0);
  for (let i = 1; i <= r; i++) {
    const row = parseLine(lines[i]);
    const sum = row.reduce((p, c) => p + c);
    row.push(sum);
    for (let j = 0; j < c + 1; j++) {
      sumRow[j] = sumRow[j] + row[j];
    }
    console.log(row.join(" "));
  }
  console.log(sumRow.join(" "));
});

function parseLine(s) {
  return s.split(" ").map((s) => Number(s));
}

