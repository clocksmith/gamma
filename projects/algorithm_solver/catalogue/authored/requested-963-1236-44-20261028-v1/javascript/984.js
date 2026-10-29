"use strict";
function solve(a,b){const out=[];while(a||b){let chooseA=a>=b;if(out.length>=2&&out[out.length-1]===out[out.length-2])chooseA=out[out.length-1]!=='a';if(chooseA){out.push('a');a--;}else{out.push('b');b--;}}return out.join('');}

function strWithout3a3b(a, b){return solve(a, b);}
module.exports=solve;
module.exports.strWithout3a3b=strWithout3a3b;
