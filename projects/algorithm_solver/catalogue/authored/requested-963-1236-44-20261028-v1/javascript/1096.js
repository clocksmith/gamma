"use strict";
function solve(expression){let at=0;function union(){const out=concat();while(at<expression.length&&expression[at]===','){at++;for(const x of concat())out.add(x);}return out;}function concat(){let out=new Set(['']);while(at<expression.length&&expression[at]!=='}'&&expression[at]!==','){let part;if(expression[at]==='{'){at++;part=union();at++;}else part=new Set([expression[at++]]);const next=new Set();for(const a of out)for(const b of part)next.add(a+b);out=next;}return out;}return [...union()].sort();}

function braceExpansionII(expression){return solve(expression);}
module.exports=solve;
module.exports.braceExpansionII=braceExpansionII;
