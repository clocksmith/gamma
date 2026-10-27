// Original candidate. Contract: https://leetcode.com/problems/check-for-contradictions-in-equations/
"use strict";
function solve(equations,values){const g=new Map();for(let i=0;i<equations.length;i++){const[a,b]=equations[i],value=values[i],st=[[a,1]],seen=new Set([a]);let found=null;while(st.length){const[u,ratio]=st.pop();if(u===b){found=ratio;break;}for(const[v,w]of g.get(u)||[])if(!seen.has(v)){seen.add(v);st.push([v,ratio*w]);}}if(found!==null&&Math.abs(found-value)>=1e-5)return true;if(!g.has(a))g.set(a,[]);if(!g.has(b))g.set(b,[]);g.get(a).push([b,value]);g.get(b).push([a,1/value]);}return false;}
module.exports = solve;
