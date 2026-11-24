"use strict";
var input=require("fs").readFileSync("/dev/stdin","utf8");
var cin=input.split(/ |\n/),cid=0;
function next(a){return a?cin[cid++]:+cin[cid++];}
function nexts(n,a){return a?cin.slice(cid,cid+=n):cin.slice(cid,cid+=n).map(a=>+a);}
function nextm(h,w,a){var r=[],i=0;if(a)for(;i<h;i++)r.push(cin.slice(cid,cid+=w));else for(;i<h;i++)r.push(cin.slice(cid,cid+=w).map(a=>+a));return r;}
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill().map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill().map(x=>"+r+")";return eval(r);}

function mul(a,b){
  var ah = a >> 16, al = a & 0xffff;
  var h = ah * b, l = al * b;
  l += 0x10000 * (h & 0xffff), h = Math.floor(h / 0x10000);
  h += Math.floor(l / 0x100000000);
  return [l>>>0,h];
}
function add(a,b){
  var l = a[0]+b[0], h = a[1]+b[1];
  if(l > 0xffffffff)h++, l -= 0x100000000;
  return [l,h>>0];
}
function minus(a,b){
  var l = a[0]-b[0], h = a[1]-b[1];
  if(l < 0)h--, l += 0x100000000;
  return [l,h>>0];
}
function half(a){
  return [(a[0]>>>1) + (a[1]&1 ? 0x80000000 : 0),a[1]>>1];
}
function compare(a,b){
  if(a[1]>b[1])return 1;
  if(a[1]<b[1])return -1;
  if(a[0]>b[0])return 1;
  if(a[0]<b[0])return -1;
  return 0;
}
function toString(a){
  var neg = 0;
  if(a[1] < 0){
    neg = 1, a[1] = -a[1];
    if(a[0])a[0] = 0x100000000 - a[0], a[1]--;
  }
  var ih = 42949, il = 67296;
  var al = a[1] * il + a[0], ah = a[1] * ih + Math.floor(al / 100000);
  al %= 100000;
  var res = "";
  if(ah === 0)res += al;
  else{
    al = ("00000" + al).slice(-5);
    res = ah + al;
  }
  if(neg && res !== "0")res = "-" + res;
  return res;
}

var zero = 0, neg = [], pos = [];
var nsize, psize;

var myOut = main();
if(myOut !== undefined)console.log(myOut);

function main(){
  var n = next(), k = next();
  for(var i = 0; i < n; i++){
    var a = next();
    if(a === 0)zero++;
    else if(a < 0)neg.push(a);
    else pos.push(a);
  }
  nsize = neg.length, psize = pos.length;
  neg.sort((a,b)=>a-b);
  pos.sort((a,b)=>a-b);
  var u = nsize * psize;
  if(k <= u)return negsolve(k);
  u += (2*n - zero - 1) * zero / 2;
  if(k <= u)return 0;
  return possolve(k-u);
}

function negsolve(k){
  var ok = [0xffffffff,-1], ng = add(ok,mul(-1e9,1e9));
  while(compare(minus(ok,ng),[1,0]) === 1){
    var m = half(add(ok,ng)), cnt = 0, l = 0;
    for(var i = 0; i < psize && cnt < k; i++){
      while(l < nsize && compare(mul(neg[l],pos[i]), m) <= 0)l++;
      cnt += l;
    }
    if(k <= cnt)ok = m; else ng = m;
  }
  return toString(ok);
}

function possolve(k){
  neg.reverse();
  var ok = mul(1e9,1e9), ng = [0,0];
  while(compare(minus(ok,ng),[1,0]) === 1){
    var m = half(add(ok,ng)), cnt = 0;
    for(var i = 0, l = psize-1; i < psize && cnt < k; i++){
      while(l > i && compare(mul(pos[l],pos[i]), m) > 0)l--;
      if(l <= i)break;
      cnt += l-i;
    }
    for(var i = 0, l = nsize-1; i < nsize && cnt < k; i++){
      while(l > i && compare(mul(neg[l],neg[i]), m) > 0)l--;
      if(l <= i)break;
      cnt += l-i;
    }
    if(k <= cnt)ok = m; else ng = m;
  }
  return toString(ok);
}