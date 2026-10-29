"use strict";
function solve(root,distance){
 const histograms=new Map(),stack=[[root,false]];let answer=0;
 while(stack.length){const [node,ready]=stack.pop();if(node===null)continue;
  if(!ready){stack.push([node,true],[node.right,false],[node.left,false]);continue;}
  const counts=Array(distance).fill(0);
  if(node.left===null&&node.right===null)counts[0]=1;
  else{const left=histograms.get(node.left)||Array(distance).fill(0),right=histograms.get(node.right)||Array(distance).fill(0);histograms.delete(node.left);histograms.delete(node.right);
   for(let a=0;a<distance;a++)for(let b=0;b<distance;b++)if(a+b+2<=distance)answer+=left[a]*right[b];
   for(let depth=1;depth<distance;depth++)counts[depth]=left[depth-1]+right[depth-1];
  }histograms.set(node,counts);
 }return answer;
}
function countPairs(root,distance){return solve(root,distance);}
module.exports=solve;module.exports.countPairs=countPairs;
