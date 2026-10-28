function solve(nums1,nums2){
 const key=a=>a.join(','),start=nums1.slice(),target=nums2.slice(),n=start.length;if(key(start)===key(target))return 0;
 let front=[start],back=[target],own=new Map([[key(start),0]]),other=new Map([[key(target),0]]);
 while(front.length&&back.length){if(front.length>back.length){[front,back]=[back,front];[own,other]=[other,own];}const following=[];
  for(const row of front){const distance=own.get(key(row))+1;for(let left=0;left<n;left++)for(let right=left+1;right<=n;right++){const block=row.slice(left,right),rest=row.slice(0,left).concat(row.slice(right));for(let p=0;p<=rest.length;p++){const next=rest.slice(0,p).concat(block,rest.slice(p)),id=key(next);if(own.has(id))continue;if(other.has(id))return distance+other.get(id);own.set(id,distance);following.push(next);}}}front=following;
 }return -1;
}

var minSplitMerge = solve;
module.exports = solve;
