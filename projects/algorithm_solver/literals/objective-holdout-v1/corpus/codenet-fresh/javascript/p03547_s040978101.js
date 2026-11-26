"use strict"

function main(input) {
  input = input.split(" ").map(v => v.charCodeAt())
  const x = input[0]
  const y = input[1]

  if (x == y) {
    console.log("=")
  } else if (x > y) {
    console.log(">")
  } else {
    console.log("<")
  }
}
main(require("fs").readFileSync("/dev/stdin", "utf8"));