function main(input) {
  const args = input.split("\n");
  let n, m, l;
  [n, m, l] = args[0].split(" ").map((x) => Number(x));

  let A = Array.from(new Array(n), () => new Array(m).fill(0));
  let B = Array.from(new Array(m), () => new Array(l).fill(0));

  for (let y = 0; y < n; y++) {
    let tmp = args[y + 1].split(" ");
    for (let x = 0; x < m; x++) {
      A[y][x] = Number(tmp[x]);
    }
  }

  for (let y = 0; y < m; y++) {
    let tmp = args[y + n + 1].split(" ");
    for (let x = 0; x < l; x++) {
      B[y][x] = Number(tmp[x]);
    }
  }

  for (let y = 0; y < n; y++) {
    let output = "";
    for (let x = 0; x < l; x++) {
      let sum = 0;
      for (let i = 0; i < m; i++) {
        sum += A[y][i] * B[i][x];
      }
      output += String(sum);
      if (x != l - 1) {
        output += " ";
      }
    }
    console.log(output);
  }
}

main(require("fs").readFileSync("/dev/stdin", "utf8"));
