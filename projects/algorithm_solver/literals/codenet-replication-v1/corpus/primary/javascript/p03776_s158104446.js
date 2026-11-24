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
  var n = next(), a = next(), b = next();
  var v = nexts(n);
  v.sort((a,b)=>b-a);
  var tot = 0;
  for(var i = 0; i < a; i++)tot += v[i];
  console.log(tot/a);
  var cnt = 0;
  if(v[0] === v[a-1]){
    var x = a;
    for(var i = a; i < n; i++){
      if(v[i] === v[a-1])x++;
    }
    for(var i = a; i <= b && i <= x; i++)cnt += ncr(x,i);
  }else{
    var x = 0;
    for(var i = 0; i < n; i++){
      if(v[i] === v[a-1])cnt++;
      else if(v[i] > v[a-1])x++;
    }
    cnt = ncr(cnt,a-x);
  }
  return cnt;
}
function ncr(n,r){
  var res = 1;
  if(r > n-r)r = n-r;
  for(var i = 1; i <= r; i++)res *= n-r+i, res /= i;
  return res;
}