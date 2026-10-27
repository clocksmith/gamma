/**
 * 4035. Maximum Valid Split Positions I
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/maximum-valid-split-positions-i/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4035.Maximum%20Valid%20Split%20Positions%20I/README_EN.md
 * Complexity: O(n + log(M) log(n)) GCD operations, O(n) space; each GCD costs O(log(M)).
 * Only prefix/suffix-GCD change indices can improve the score. A deleted leaf is represented by neutral zero. Prefix/suffix descent locates all valid boundaries; an interior zero duplicates exactly one boundary, which is subtracted. Inputs preserved.
 */

function solve(nums) {
  function gcd(a,b) { while(b) { const t=a%b; a=b;b=t; } return a; }
  const n=nums.length; let size=1;
  while(size<n) size*=2;
  const tree=new Float64Array(2*size), candidates=new Set();
  tree.set(nums,size);
  for(let i=size-1;i>0;i--) tree[i]=gcd(tree[2*i],tree[2*i+1]);
  let current=0;
  for(let i=0;i<n;i++) { const next=gcd(current,nums[i]); if(next!==current)candidates.add(i);current=next; }
  current=0;
  for(let i=n-1;i>=0;i--) { const next=gcd(current,nums[i]);if(next!==current)candidates.add(i);current=next; }
  function put(index,value) {
    let p=size+index;tree[p]=value;
    while(p>1) { p=Math.floor(p/2);tree[p]=gcd(tree[2*p],tree[2*p+1]); }
  }
  function score(deleted=-1) {
    const target=tree[1];let p=1,acc=0;
    while(p<size) { const q=2*p, value=gcd(acc,tree[q]);if(value===target)p=q;else {acc=value;p=q+1;} }
    const first=p-size;p=1;acc=0;
    while(p<size) { const q=2*p+1,value=gcd(acc,tree[q]);if(value===target)p=q;else {acc=value;p=q-1;} }
    const last=p-size;
    return Math.max(0,last-first)-Number(first<deleted && deleted<last);
  }
  let answer=score();
  for(const index of candidates) { put(index,0);answer=Math.max(answer,score(index));put(index,nums[index]); }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
