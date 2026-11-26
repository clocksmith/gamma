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
  var NN = "No", YY = "Yes";
  var n = next();
  var up = [], ud = [], sum = 0, rest = 0;
  for(var i = 0; i < n; i++){
    var mn = 0, last = 0;
    var s = next(1);
    for(var j = 0; j < s.length; j++){
      if(s[j] === "(")last++;
      else{
        last--;
        if(last < mn)mn = last;
      }
    }
    sum += last;
    if(mn >= 0)rest += last;
    else if(last <= 0)up.push([-mn+last,last]);
    else ud.push([-mn,last]);
  }
  if(sum)return NN;
  ud.sort((a,b)=>a[0]-b[0]);
  for(var i = 0; i < ud.length; i++){
    if(ud[i][0] > rest)return NN;
    rest += ud[i][1];
  }
  up.sort((a,b)=>b[0]-a[0]);
  for(var i = 0; i < up.length; i++){
    var [mn,last] = up[i];
    if(mn-last > rest)return NN;
    rest += last;
  }
  return YY;
}