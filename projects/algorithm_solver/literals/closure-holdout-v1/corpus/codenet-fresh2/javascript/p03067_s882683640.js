"use strict";

function Main(input) {
  input = input.split(" ");
  var A = parseInt(input[0], 10);
  var B = parseInt(input[1], 10);
  var C = parseInt(input[2], 10);

  if (A < C && C < B) {
    console.log("Yes");
    return;
  } else if (B < C && C < A) {
    console.log("Yes");
    return;
  }

  console.log("No");
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));