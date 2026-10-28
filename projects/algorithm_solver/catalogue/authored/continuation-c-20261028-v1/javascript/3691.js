class MinHeap {
 constructor(){this.a=[];}
 push(item){const a=this.a;a.push(item);let i=a.length-1;while(i){const p=(i-1)>>1;if(a[p][0]<=item[0])break;a[i]=a[p];i=p;}a[i]=item;}
 pop(){const a=this.a,first=a[0],last=a.pop();if(a.length){let i=0;while(2*i+1<a.length){let c=2*i+1;if(c+1<a.length&&a[c+1][0]<a[c][0])c++;if(a[c][0]>=last[0])break;a[i]=a[c];i=c;}a[i]=last;}return first;}
}
function solve(nums,k){
 const n=nums.length,high=[nums.slice()],low=[nums.slice()],logs=Array(n+1).fill(0);for(let i=2;i<=n;i++)logs[i]=logs[Math.floor(i/2)]+1;
 for(let shift=1;2*shift<=n;shift*=2){const ph=high[high.length-1],pl=low[low.length-1],h=[],l=[];for(let i=0;i+2*shift<=n;i++){h.push(Math.max(ph[i],ph[i+shift]));l.push(Math.min(pl[i],pl[i+shift]));}high.push(h);low.push(l);}
 function value(left,right){const level=logs[right-left+1],offset=right-2**level+1;return Math.max(high[level][left],high[level][offset])-Math.min(low[level][left],low[level][offset]);}
 const heap=new MinHeap();for(let left=0;left<n;left++)heap.push([-value(left,n-1),left,n-1]);let answer=0;for(let i=0;i<k;i++){const [negative,left,right]=heap.pop();answer-=negative;if(right>left)heap.push([-value(left,right-1),left,right-1]);}return answer;
}

var maxTotalValue = solve;
module.exports = solve;
