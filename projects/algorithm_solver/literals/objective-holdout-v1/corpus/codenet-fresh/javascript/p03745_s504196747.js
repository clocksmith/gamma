"use strict";

(function(stdin){
  let input = stdin.split("\n");
  // 10進数に変換
  let n = parseInt(input[0], 10);
  let a = input[1].split(" ");

  for (let i = 0; i < n; i++) {
    a[i] = parseInt(a[i], 10);
  }

  let ans = 0;
  let up = false;
  let down = false;
  for (let i = 0; i < n - 1; i++) {
    if (a[i] < a[i + 1]) {
      up = true;
    }
    if (a[i] > a[i + 1]) {
      down = true;
    }
    if (up && down) {
      up = down = false;
      ans++;
    }
  }

  console.log(ans + 1);
})(require("fs").readFileSync("/dev/stdin", "utf8"));