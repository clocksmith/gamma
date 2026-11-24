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
  var n = next(), m = next();
  var g = xArray("[]",n);
  for(var i = 0; i < m; i++){
    var a = next()-1, b = next()-1;
    g[a].push(b);
    g[b].push(a);
  }
  var q = next();
  var r = nextm(q,3);
  var dp = xArray(-1,11,n);
  for(var i = q; i--;){
    var x = [r[i][0]-1,r[i][1]],id=0;
    while(x.length > id){
      var v = x[id], d = x[id+1];
      id += 2;
      if(dp[d][v] >= i)continue;
      for(var j = d; j >= 0; j--){
        if(dp[j][v] < i)dp[j][v] = i;
      }
      if(d-- === 0)continue;
      for(var j = 0; j < g[v].length; j++){
        var V = g[v][j];
        if(dp[d][V] < i)x.push(V,d);
      }
    }
  }
  var ans = Array(n);
  for(var i = 0; i < n; i++)ans[i] = dp[0][i] < 0 ? 0 : r[dp[0][i]][2];
  return ans.join("\n");
}