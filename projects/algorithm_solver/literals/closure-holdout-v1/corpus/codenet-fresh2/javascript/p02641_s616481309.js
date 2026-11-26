const main = (input) => {
  const args = input.trim().split("\n");
  const [x, n] = args[0]
    .split(" ")
    .map((n) => parseInt(n, 10));
 
  const excluded = (() => {
    if (n === 0) {
      return [];
    } else {
      return args[1]
        .split(" ")
        .map((n) => parseInt(n, 10));
    }
  })();
 
  const selection = [...Array(101 + 1).keys()].filter(
    (s) => !excluded.includes(s)
  );
 
  const abs = (n) => {
    if (n < 0) return -n;
    else {
      return n;
    }
  };
  const byAsc = (a, b) => a[1] - b[1];
 
  const answer = selection
    .map((s) => [s, abs(x - s)])
    .sort(byAsc)[0][0];
 
  console.log(answer);
};
 
main(require("fs").readFileSync("/dev/stdin", "utf8"));