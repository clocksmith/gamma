"use strict";
var input=require("fs").readFileSync("/dev/stdin","utf8");
var cin=input.split(/ |\n/),cid=0;
function next(){return +cin[cid++];}
function nextstr(){return cin[cid++];}
function nextbig(){return BigInt(cin[cid++]);}
function nexts(n,a){return a?cin.slice(cid,cid+=n):cin.slice(cid,cid+=n).map(a=>+a);}
function nextm(h,w,a){var r=[],i=0;if(a)for(;i<h;i++)r.push(cin.slice(cid,cid+=w));else for(;i<h;i++)r.push(cin.slice(cid,cid+=w).map(a=>+a));return r;}
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill().map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill().map(x=>"+r+")";return eval(r);}

function gcd(a,b){return b?gcd(b,a%b):a;}

var mod = 1e9+7;
function mul(a,b){return ((a>>16)*b%mod*65536+(a&65535)*b)%mod;}
function pow(a,n){for(var r=1;n;a=mul(a,a),n>>=1)if(n&1)r=mul(a,r);return r;}
function mput(n){return (n%mod+mod)%mod;}

var myOut = main();
if(myOut !== undefined)console.log(myOut);

function main(){
  var n = next();
  var az = 0, bz = 0, z = 0;
  var map = new Map();
  for(var i = 0; i < n; i++){
    var a = nextbig(), b = nextbig();
    if(a === 0n && b === 0n){z++; continue;}
    if(a === 0n){az++; continue;}
    if(b === 0n){bz++; continue;}
    var c = gcd(a,b);
    a /= c, b /= c;
    if(a < 0)a = -a, b = -b;
    if(map.has(a)){
      if(map.get(a).has(b))map.get(a).set(b,map.get(a).get(b)+1);
      else map.get(a).set(b,1);
    }else{
      map.set(a,new Map());
      map.get(a).set(b,1);
    }
  }
  var ans = pow(2,az) + pow(2,bz) - 1;
  for(var [i0,i1] of map){
    for(var [j0,j1] of i1){
      var t = 0;
      if(j0 < 0){
        if(map.has(-j0) && map.get(-j0).has(i0))continue;
      }else{
        if(map.has(j0) && map.get(j0).has(-i0))t = pow(2,map.get(j0).get(-i0))-1;
      }
      t += pow(2,j1);
      ans = mul(ans,t);
    }
  }
  return mput(ans-1+z);
}