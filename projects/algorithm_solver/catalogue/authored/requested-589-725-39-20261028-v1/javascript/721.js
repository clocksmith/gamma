"use strict";
function solve(accounts){const parent=accounts.map((_,i)=>i);function find(i){while(parent[i]!==i){parent[i]=parent[parent[i]];i=parent[i];}return i;}const owner=new Map();for(let i=0;i<accounts.length;i++)for(const email of accounts[i].slice(1)){if(owner.has(email))parent[find(i)]=find(owner.get(email));else owner.set(email,i);}const groups=new Map();for(const [email,i]of owner){const root=find(i);if(!groups.has(root))groups.set(root,[]);groups.get(root).push(email);}const out=[];for(const [i,emails]of groups)out.push([accounts[i][0],...emails.sort()]);out.sort((a,b)=>{for(let i=0;i<Math.min(a.length,b.length);i++)if(a[i]!==b[i])return a[i]<b[i]?-1:1;return a.length-b.length;});return out;}

function accountsMerge(accounts){return solve(accounts);}
module.exports=solve;
module.exports.accountsMerge=accountsMerge;
