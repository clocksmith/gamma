"use strict";
var input=require("fs").readFileSync("/dev/stdin","utf8");
var cin=input.split(/ |\n/),cid=0;
function next(){return +cin[cid++];}
function nextstr(){return cin[cid++];}
function nextbig(){return BigInt(cin[cid++]);}
function nexts(n,a){return a?cin.slice(cid,cid+=n):cin.slice(cid,cid+=n).map(a=>+a);}
function nextm(h,w,a){var r=[],i=0;if(a)for(;i<h;i++)r.push(cin.slice(cid,cid+=w));else for(;i<h;i++)r.push(cin.slice(cid,cid+=w).map(a=>+a));return r;}
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill().map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill().map(x=>"+r+")";return eval(r);}

var myOut = main();
if(myOut !== undefined)console.log(myOut);

function main(){
  var h = next(), w = next();
  var a = nexts(h,1);
  var ans1 = xArray("'.'",h,w);
  var ans2 = xArray("'.'",h,w);
  for(var i = 0; i < h; i++){
    ans1[i][0] = ans2[i][w-1] = "#";
    for(var j = 1; j < w-1; j++){
      if(i & 1)ans1[i][j] = "#";
      else ans2[i][j] = "#";
      if(a[i][j] === ".")continue;
      ans1[i][j] = ans2[i][j] = "#";
    }
  }
  console.log(ans1.map(a=>a.join("")).join("\n"));
  console.log("");
  return ans2.map(a=>a.join("")).join("\n");
}