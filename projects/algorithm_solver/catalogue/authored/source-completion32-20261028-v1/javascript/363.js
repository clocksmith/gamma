// 363 — Max Sum of Rectangle No Larger Than K. Original implementation; authored candidate, not independently qualified.
function solve(input, k) {
  const matrix = input.length > input[0].length ? input[0].map((_,c) => input.map(row => row[c])) : input;
  const rows = matrix.length, cols = matrix[0].length; let best = -Infinity;
  const lowerBound = (a, v) => { let lo=0,hi=a.length; while(lo<hi){const m=Math.floor((lo+hi)/2);if(a[m]<v)lo=m+1;else hi=m;} return lo; };
  for (let top=0;top<rows;top++) {
    const sums=Array(cols).fill(0);
    for(let bottom=top;bottom<rows;bottom++) {
      for(let c=0;c<cols;c++)sums[c]+=matrix[bottom][c];
      const prefixes=[0];let current=0;
      for(const value of sums){current+=value;const i=lowerBound(prefixes,current-k);if(i<prefixes.length){best=Math.max(best,current-prefixes[i]);if(best===k)return k;}prefixes.splice(lowerBound(prefixes,current),0,current);}
    }
  }
  return best;
}

module.exports = { solve, maxSumSubmatrix: solve };
