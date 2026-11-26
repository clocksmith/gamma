"use strict";
var input=require("fs").readFileSync("/dev/stdin","utf8");
var cin=input.split(/ |\n/),cid=0;
function next(a){return a?cin[cid++]:+cin[cid++];}
function nexts(n,a){return a?cin.slice(cid,cid+=n):cin.slice(cid,cid+=n).map(a=>+a);}
function nextm(h,w,a){var r=[],i=0;if(a)for(;i<h;i++)r.push(cin.slice(cid,cid+=w));else for(;i<h;i++)r.push(cin.slice(cid,cid+=w).map(a=>+a));return r;}
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill().map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill().map(x=>"+r+")";return eval(r);}

var myOut = main();
if(myOut !== undefined)console.log(myOut);

function main(){
  var n = next(), k = next(), c = next();
  var s = next(1);
  var l = xArray(0,n), t = 1;
  for(var i = 0; i < n; i++){
    if(s[i] === "o")l[i] = t++, i += c;
  }
  t = k;
  var r = xArray(0,n);
  for(var i = n; i-- > 0;){
    if(s[i] === "o")r[i] = t--, i -= c;
  }
  var ans = [];
  for(var i = 0; i < n; i++){
    if(l[i] && l[i] === r[i])ans.push(i+1);
  }
  if(ans.length)return ans.join("\n")
}