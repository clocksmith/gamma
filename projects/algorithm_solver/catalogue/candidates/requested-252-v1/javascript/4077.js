/**
 * 4077. Minimize Inversions in a Prefix Tree
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimize-inversions-in-a-prefix-tree/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4077.Minimize%20Inversions%20in%20a%20Prefix%20Tree/README_EN.md
 * Complexity: O(10L + sum_v d_v*2^d_v) time, O(L + sum_v d_v^2 + 10*2^10) space; L total word length, d_v<=10.
 * A pair in different child subtrees is charged once at its LCA. Child ordering costs depend only on subtree rank sets, so each branching node is optimized independently with subset DP. Marked-prefix/descendant pairs have fixed preorder and are counted separately. Inputs preserved.
 */

function solve(words,target) {
  const children=[new Map()];
  for(const word of words) {
    let node=0;
    for(const character of word) {
      if(!children[node].has(character)) {const entry=[children.length,children[node].size];children[node].set(character,entry);children.push(new Map());}
      node=children[node].get(character)[0];
    }
  }
  const degrees=children.map(x=>x.size);
  const seen=degrees.map(d=>d>1?new Int32Array(d):null),cross=degrees.map(d=>d>1?new Float64Array(d*d):null);
  const total=new Int32Array(children.length);let answer=0;
  for(const wordIndex of target) {
    let node=0;
    for(const character of words[wordIndex]) {
      const [child,branch]=children[node].get(character),d=degrees[node];
      if(d>1){for(let other=0;other<d;other++)if(other!==branch)cross[node][branch*d+other]+=seen[node][other];seen[node][branch]++;}
      total[node]++;node=child;
    }
    answer+=total[node];total[node]++;
  }
  for(let node=0;node<children.length;node++) {
    const d=degrees[node];if(d<2)continue;
    const costs=cross[node];if(d===2){answer+=Math.min(costs[1],costs[2]);continue;}
    const size=1<<d,incoming=Array.from({length:d},()=>new Float64Array(size));
    for(let last=0;last<d;last++)for(let mask=1;mask<size;mask++) {
      const low=mask&-mask,first=31-Math.clz32(low);
      incoming[last][mask]=incoming[last][mask-low]+costs[first*d+last];
    }
    const best=new Float64Array(size);best.fill(Infinity);best[0]=0;
    for(let mask=1;mask<size;mask++) {
      let bits=mask;
      while(bits){const low=bits&-bits,last=31-Math.clz32(low),previous=mask-low;best[mask]=Math.min(best[mask],best[previous]+incoming[last][previous]);bits-=low;}
    }
    answer+=best[size-1];
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
