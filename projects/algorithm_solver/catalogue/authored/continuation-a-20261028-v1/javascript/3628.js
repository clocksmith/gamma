function solve(s) {
  let rightT = 0;
  for (const c of s) if (c === 'T') rightT++;
  let leftL = 0, lc = 0, ct = 0, existing = 0, insertC = 0;
  for (const c of s) {
    insertC = Math.max(insertC, leftL * rightT);
    if (c === 'L') leftL++;
    else if (c === 'C') { lc += leftL; ct += rightT; }
    else if (c === 'T') { existing += lc; rightT--; }
  }
  insertC = Math.max(insertC, leftL * rightT);
  return existing + Math.max(lc, ct, insertC);
}

var numOfSubsequences = solve;
module.exports = solve;
