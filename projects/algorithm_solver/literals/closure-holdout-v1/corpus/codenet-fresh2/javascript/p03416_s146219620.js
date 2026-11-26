"use strict";

function main(input) {
  input = input.split(/\n|\s/).map(v => ~~v);
  const a = input[0];
  const b = input[1];

  let i = a;
  let ans = 0;
  while (i <= b) {
    if (
      Math.floor(i / 10000) === i % 10 &&
      Math.floor(i / 1000) % 10 === Math.floor(i / 10) % 10
    )
      ans++;

    i++;
  }
  console.log(ans);
}

main(require("fs").readFileSync("/dev/stdin", "utf8"));
