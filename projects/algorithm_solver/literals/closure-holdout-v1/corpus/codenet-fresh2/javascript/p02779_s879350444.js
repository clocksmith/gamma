"use strict";

const main = arg => {
    // 標準入力の不要な空白と改行を削除し、配列に格納する
    const input = arg.trim().split("\n");
    const nums = input[1].split(" ");

    const set = new Set(nums);
    const uniqueNums = Array.from(set);

    nums.length === uniqueNums.length ? console.log("YES") : console.log("NO");
}

main(require('fs').readFileSync('/dev/stdin', 'utf8'));  