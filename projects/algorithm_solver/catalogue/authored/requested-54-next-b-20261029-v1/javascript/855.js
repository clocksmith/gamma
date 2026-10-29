"use strict";
class ExamRoom {
 constructor(n){this.n=n;this.occupied=[];}
 seat(){const a=this.occupied;let seat=0,distance=a.length?a[0]:this.n;
  for(let i=1;i<a.length;i++){const candidate=Math.floor((a[i]-a[i-1])/2);if(candidate>distance){seat=a[i-1]+candidate;distance=candidate;}}
  if(a.length&&this.n-1-a[a.length-1]>distance)seat=this.n-1;
  let lo=0,hi=a.length;while(lo<hi){const mid=(lo+hi)>>1;if(a[mid]<seat)lo=mid+1;else hi=mid;}a.splice(lo,0,seat);return seat;
 }
 leave(p){this.occupied.splice(this.occupied.indexOf(p),1);}
}
module.exports={ExamRoom};
