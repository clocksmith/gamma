"use strict";
class RangeModule{constructor(){this.intervals=[];}addRange(left,right){const out=[];let inserted=false;for(const [a,b]of this.intervals){if(b<left)out.push([a,b]);else if(right<a){if(!inserted){out.push([left,right]);inserted=true;}out.push([a,b]);}else{left=Math.min(left,a);right=Math.max(right,b);}}if(!inserted)out.push([left,right]);this.intervals=out;}queryRange(left,right){for(const [a,b]of this.intervals){if(a<=left&&right<=b)return true;if(a>left)return false;}return false;}removeRange(left,right){const out=[];for(const [a,b]of this.intervals){if(b<=left||right<=a)out.push([a,b]);else{if(a<left)out.push([a,left]);if(right<b)out.push([right,b]);}}this.intervals=out;}}

function solve(operations,args){const instance=new RangeModule(...args[0]),out=[null];for(let i=1;i<operations.length;i++){const result=instance[operations[i]](...args[i]);out.push(result===undefined?null:result);}return out;}
module.exports=solve;
module.exports.RangeModule=RangeModule;
