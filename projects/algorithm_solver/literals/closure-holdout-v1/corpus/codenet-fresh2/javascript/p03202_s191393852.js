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
  var n = next();
  var a = nexts(n);
  var ok = n, ng = 0;
  while(ok-ng > 1){
    var m = ok+ng >> 1, f = 1;
    var b;
    if(a[0] > 1)b = [1,1,a[0],1]; else b = [1,1];
    for(var i = 1; i < n && f; i++){
      if(b[b.length-2] < a[i]){
        b.push(a[i],1);
      }else{
        if(m === 1){
          f = 0;
          break;
        }
        while(b[b.length-2] > a[i])b.length -= 2;
        if(b[b.length-2] < a[i])b.push(a[i],2);
        else{
          var t = b[b.length-2];
          for(var j = b.length-1; j > 0; j -= 2){
            if(b[j-1] < t){
              b.push(t,2,a[i],1);
              break;
            }
            if(b[j] < m){
              b[j]++;
              if(b[j-1] < a[i])b.push(a[i],1);
              break;
            }
            b.length -= 2;
            t--;
          }
          if(j < 0)f = 0;
        }
      }
    }
    if(f)ok = m; else ng = m;
  }
  return ok;
}