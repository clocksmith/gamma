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
  var n = next();
  var a = nexts(n);
  var s0 = 0, s1 = 0, p0 = [], p1 = [];
  for(var i = 0; i < n; i += 2)if(a[i] > 0)s0 += a[i], p0.push(i);
  for(var i = 1; i < n; i += 2)if(a[i] > 0)s1 += a[i], p1.push(i);
  if(s0 === 0 && s1 === 0)return minus(n,a);
  console.log(Math.max(s0,s1));
  if(s0 > s1)return solve(n,p0);
  return solve(n,p1);
}

function solve(n,p){
  var l = p.length-1, res = [];
  for(var i = n; i--;){
    if(l === 0){
      if(p[l] > i)res.push(1);
      else if(p[l] < i)res.push(i+1);
    }else{
      if(p[l] < i)res.push(i+1);
      else if(p[l]-2 === p[l-1]){
        res.push(p[l]);
        l--, i = p[l];
      }else{
        res.push(p[l]-1);
        p[l] -= 2;
        i = p[l];
      }
    }
  }
  console.log(res.length);
  return res.join("\n");
}

function minus(n,a){
  var id = 0, mx = a[0];
  for(var i = 1; i < n; i++){
    if(mx < a[i])mx = a[i], id = i;
  }
  var ans = [mx,n-1];
  for(var i = n; i--;){
    if(i === id)continue;
    if(i < id)ans.push(1);
    else ans.push(i+1);
  }
  return ans.join("\n");
}