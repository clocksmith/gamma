function solve(nums1, nums2) { const z=nums2[nums2.length-1]; let base=1, extra=Infinity; for(let i=0;i<nums1.length;i++){const x=nums1[i],y=nums2[i];base+=Math.abs(x-y);extra=Math.min(extra,Math.max(Math.min(x,y)-z,z-Math.max(x,y),0));}return base+extra;}

var minOperations = solve;
module.exports = solve;
