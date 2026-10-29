"use strict";
function solve(cards){function rational(n,d=1n){if(d<0n){n=-n;d=-d;}let a=n<0n?-n:n,b=d;while(b){const t=a%b;a=b;b=t;}return {n:n/a,d:d/a};}function search(vs){if(vs.length===1)return vs[0].n===24n*vs[0].d;for(let i=0;i<vs.length;i++)for(let j=i+1;j<vs.length;j++){const a=vs[i],b=vs[j],rest=vs.filter((_,k)=>k!==i&&k!==j),options=[rational(a.n*b.d+b.n*a.d,a.d*b.d),rational(a.n*b.d-b.n*a.d,a.d*b.d),rational(b.n*a.d-a.n*b.d,a.d*b.d),rational(a.n*b.n,a.d*b.d)];if(b.n)options.push(rational(a.n*b.d,a.d*b.n));if(a.n)options.push(rational(b.n*a.d,b.d*a.n));for(const x of options)if(search([...rest,x]))return true;}return false;}return search(cards.map(x=>rational(BigInt(x))));}

function judgePoint24(cards){return solve(cards);}
module.exports=solve;
module.exports.judgePoint24=judgePoint24;
