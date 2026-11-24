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
if(myOut !== undefined)console.log(String(myOut));

function main(){
  var k = 38;
  var n = k*k-k+1;
  var ans = xArray("[]",n);
  for(var i = 0; i < k; i++){
    ans[i].push(1);
    for(var j = 2; j <= k; j++){
      ans[i].push(i*(k-1)+j);
    }
  }
  for(var i = 1; i < k; i++){
    for(var j = 1; j < k; j++){
      var y = j + i*(k-1);
      var p = k+1;
      var q = j-1;
      ans[y].push(i+1);
      for(var x = 1; x < k; x++){
        ans[y].push(p+q);
        p += k-1;
        q += i-1;
        q %= k-1;
      }
    }
  }
  console.log(n,k);
  return ans.map(a=>a.join(" ")).join("\n");
}