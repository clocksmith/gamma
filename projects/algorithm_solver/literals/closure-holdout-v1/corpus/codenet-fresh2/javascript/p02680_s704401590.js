"use strict";
var input=require("fs").readFileSync("/dev/stdin","utf8");
var cin=input.split(/ |\n/),cid=0;
function next(){return +cin[cid++];}
function nextstr(){return cin[cid++];}
function nextbig(){return BigInt(cin[cid++]);}
function nexts(n,a){return a?cin.slice(cid,cid+=n):cin.slice(cid,cid+=n).map(a=>+a);}
function nextm(h,w,a){var r=[],i=0;if(a)for(;i<h;i++)r.push(cin.slice(cid,cid+=w));else for(;i<h;i++)r.push(cin.slice(cid,cid+=w).map(a=>+a));return r;}
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill().map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill().map(x=>"+r+")";return eval(r);}

function lowerBound(ary,v,l=0,r=ary.length){--l;for(var c;1<r-l;)ary[c=l+r>>1]<v?l=c:r=c;return r;}
function upperBound(ary,v,l=0,r=ary.length){--l;for(var c;1<r-l;)ary[c=l+r>>1]<=v?l=c:r=c;return r;}
function griddist(grid,startx,starty){
  const road = ".", wall = "#", INF = 1e9;
  const h = grid.length, w = grid[0].length;
  const res = Array(h).fill().map(a=>Array(w).fill(INF));
  const dx = [0, 1, 0, -1], dy = [-1, 0, 1, 0], dd = 4;
  var q = [startx, starty], dist = 1;
  res[starty][startx] = 0;
  while(q.length){
    var qq = [];
    while(q.length){
      var y = q.pop(), x = q.pop();
      for(var i = 0; i < dd; i++){
        var xx = x+dx[i], yy = y+dy[i];
        if(xx < 0 || xx === w || yy < 0 || yy === h)continue;
        if(grid[yy][xx] === wall || res[yy][xx] !== INF)continue;
        res[yy][xx] = dist;
        qq.push(xx,yy);
      }
    }
    dist++, q = qq;
  }
  return res;
}

var myOut = main();
if(myOut !== undefined)console.log(myOut);

function main(){
  var [n,m] = nexts(2);
  var setx = new Set([0]), sety = new Set([0]);
  var xl = nextm(n,3).sort((a,b)=>a[2]-b[2]);
  var yl = nextm(m,3).sort((a,b)=>a[0]-b[0]);
  for(var i = 0; i < n; i++)setx.add(xl[i][2]);
  for(var i = 0; i < m; i++)sety.add(yl[i][0]);
  var gx = Array.from(setx).sort((a,b)=>a-b);
  var gy = Array.from(sety).sort((a,b)=>a-b);
  var w = gx.length * 2 + 1;
  var h = gy.length * 2 + 1;
  var grid = xArray("'.'",h,w);
  var dh = xArray(0,h), dw = xArray(0,w);
  for(var i = 1; i < gx.length; i++)dw[i+i] = gx[i]-gx[i-1];
  for(var i = 1; i < gy.length; i++)dh[i+i] = gy[i]-gy[i-1];
  var id = 0;
  for(var i = 0; i < n; i++){
    while(gx[id] < xl[i][2])id++;
    var t = id+id+1;
    var u = lowerBound(gy,xl[i][0])*2+1;
    var d = upperBound(gy,xl[i][1])*2-1;
    for(; u <= d; u++)grid[u][t] = "#";
  }
  for(var i = 0, id = 0; i < m; i++){
    while(gy[id] < yl[i][0])id++;
    var t = id+id+1;
    var l = lowerBound(gx,yl[i][1])*2+1;
    var r = upperBound(gx,yl[i][2])*2-1;
    for(; l <= r; l++)grid[t][l] = "#";
  }
  var dist = griddist(grid,lowerBound(gx,0)*2+1,lowerBound(gy,0)*2+1);
  if(dist[0][0] < 1e9)return "INF";
  var sumy = xArray(0,h);
  for(var y = 2; y < dh.length-2; y += 2)
  for(var x = 2; x < dw.length-2; x += 2){
    if(dist[y][x] === 1e9)continue;
    sumy[y] += dw[x];
  }
  var ans = 0n;
  for(var y = 2; y < dh.length-2; y += 2)ans += BigInt(sumy[y]) * BigInt(dh[y]);
  return ans.toString();
}