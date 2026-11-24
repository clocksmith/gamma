"use strict"

const main = arg => {
  arg = arg.trim().split("\n");

  const n = ~~(arg[0].split(" ")[0]);
  const m = ~~(arg[0].split(" ")[1]);

  const a = arg.slice(1, n + 1).map(n=>n.split(""));
  const b = arg.slice(n + 1, (n + 1) + (m + 1)).map(n=>n.split(""));

  let answer = false;

  const A = [];
  const B = [];

  for (let i=0; i<m; i++) {
    for (let j=0; j<m; j++) {
      A.push(i);
      B.push(j);
    }
  }
  
  for (let i=0; i<n; i++) {
    for (let j=0; j<n; j++) {
      
      for (let k=0, len=Math.pow(m, 2); k<len; k++) {
        const X = i + A[k];
        const Y = j + B[k];
        
        if (X < 0 || n <= X) break;
        if (Y < 0 || n <= Y) break;
        if (a[X][Y] !== b[A[k]][B[k]]) break;

        if (k === (len - 1)) answer = true;
      }
    }
  }

  console.log(answer ? "Yes" : "No");
}

main(require("fs").readFileSync("/dev/stdin", "utf8"));