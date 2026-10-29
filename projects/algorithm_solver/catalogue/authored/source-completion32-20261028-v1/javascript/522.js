// 522 — Longest Uncommon Subsequence II. Original implementation; authored candidate, not independently qualified.
function solve(strs) {
  function subsequence(a,b){let i=0;for(const char of b)if(i<a.length&&a[i]===char)i++;return i===a.length;}
  let answer=-1;strs.forEach((word,i)=>{if(word.length>answer&&strs.every((other,j)=>i===j||!subsequence(word,other)))answer=word.length;});return answer;
}

module.exports = { solve, findLUSlength: solve };
