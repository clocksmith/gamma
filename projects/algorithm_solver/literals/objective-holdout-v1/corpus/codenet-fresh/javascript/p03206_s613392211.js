"use strict";
process.stdin.resume();
process.stdin.setEncoding('utf8');

var reader = require('readline').createInterface({
  input: process.stdin,
  output: process.stdout
});
reader.on('line', (line) => {
    let d = line;
    let diff = 25 - d;
    let ans = "Christmas";
    
    for (let i = 0; i < diff; i++) {
      ans += " Eve"
    }

    console.log(ans);
});
