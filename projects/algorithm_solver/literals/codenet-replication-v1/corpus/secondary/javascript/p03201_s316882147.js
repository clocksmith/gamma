"use strict";

function binarySearch(arr, val) {
  let start = 0;
  let end = arr.length - 1;

  while (start <= end) {
    let mid = Math.floor((start + end) / 2);
    // console.log(mid);

    if (arr[mid] === val && (mid === 0 || arr[mid - 1] > val)) {
      return mid;
    }
    if (val >= arr[mid]) {
      end = mid - 1;
    } else {
      start = mid + 1;
    }
  }
  return -1;
}

function main(input) {
  const inputs = input.split("\n").filter(x => x !== "");
  const A = inputs[1].split(" ").map(Number);

  let sortedA = A.sort((a, b) => b - a);
  let count = 0;
  let num2n = Math.pow(2, sortedA[0].toString(2).length);

  let start, end;

  for (let index = 0; index < sortedA.length; index++) {
    let i = sortedA[index];
    if (i === -1) continue;
    sortedA[index] = Number.MAX_VALUE;

    while (num2n > 2 * i) {
      num2n = num2n / 2;
    }

    let j = num2n - i;
    let indexJ = binarySearch(sortedA, j);

    if (indexJ >= 0) {
      sortedA[indexJ] = sortedA[indexJ] + 0.1;
      count++;
    }

    // console.log({ i, j, indexJ, sortedA });
  }

  console.log(count);
}

main(require("fs").readFileSync("/dev/stdin", "utf8"));
