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
  const inf = 1e9;
  const dx = [0,1,0,-1], dy = [-1,0,1,0], dd = 4;
  var [h,w,k] = nexts(3);
  var [sy,sx,gy,gx] = nexts(4);
  var c = Array(h+2);
  c[0] = xArray("'@'",w+2).join("");
  for(var i = 0; i < h; i++)c[i+1] = "@"+nextstr()+"@";
  c[h+1] = xArray("'@'",w+2).join("");
  var dist = xArray(inf,h+2,w+2);
  dist[sy][sx] = 0;
  var q = [sy,sx], d = 0;
  while(q.length){
    var p = [];
    while(q.length){
      var x = q.pop(), y = q.pop();
      for(var i = 0; i < dd; i++){
        var xx = x, yy = y;
        for(var j = 0; j < k; j++){
          xx += dx[i], yy += dy[i];
          if(c[yy][xx] === "@")break;
          if(dist[yy][xx] <= d)break;
          if(dist[yy][xx] > d+1)p.push(yy,xx),dist[yy][xx] = d+1;
         }
      }
    }
    q = p, d++;
  }
  return dist[gy][gx] === inf ? -1 : dist[gy][gx];
}