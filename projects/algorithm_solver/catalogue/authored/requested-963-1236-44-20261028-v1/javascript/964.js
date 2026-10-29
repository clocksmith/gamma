"use strict";
function solve(x,target){let digit=target%x,positive=2*digit,negative=2*(x-digit),power=1;target=Math.floor(target/x);while(target){digit=target%x;const p=Math.min(positive+digit*power,negative+(digit+1)*power),n=Math.min(positive+(x-digit)*power,negative+(x-digit-1)*power);positive=p;negative=n;target=Math.floor(target/x);power++;}return Math.min(positive,negative+power)-1;}

function leastOpsExpressTarget(x, target){return solve(x, target);}
module.exports=solve;
module.exports.leastOpsExpressTarget=leastOpsExpressTarget;
