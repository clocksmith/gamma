// Original candidate. Contract: https://leetcode.com/problems/step-by-step-directions-from-a-binary-tree-node-to-another/
"use strict";
function solve(root,startValue,destValue){const par=new Map([[root[0],[null,'']]]),q=[root[0]];let j=1;for(let i=0;i<q.length;i++){for(const d of ['L','R'])if(j<root.length){const c=root[j++];if(c!==null){par.set(c,[q[i],d]);q.push(c);}}}let u=startValue,k=0;const anc=new Map();while(u!==null){anc.set(u,k++);u=par.get(u)[0];}u=destValue;const down=[];while(!anc.has(u)){const [v,d]=par.get(u);down.push(d);u=v;}return 'U'.repeat(anc.get(u))+down.reverse().join('');}
module.exports = solve;
