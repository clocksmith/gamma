'use strict'

function Main(input) {
  let array = input.split("\n")[1].split(" ").map(e => parseInt(e, 10));
  let count = 0;
  while (array.every(e => (e % 2) === 0)) {
    array = array.map(e => e / 2);
    count++;
  }
  console.log(count);
}

//*この行以降は編集しないでください（標準入出力から一度に読み込み、Mainを呼び出します）
Main(require("fs").readFileSync("/dev/stdin", "utf8"));