"use strict";
var input=require("fs").readFileSync("/dev/stdin","utf8");
var cin=input.split(/ |\n/),cid=0;
function next(){return +cin[cid++];}
function nextstr(){return cin[cid++];}
function nextbig(){return BigInt(cin[cid++]);}
function nexts(n,a){return a?cin.slice(cid,cid+=n):cin.slice(cid,cid+=n).map(a=>+a);}
function nextssort(n,a){return a?cin.slice(cid,cid+=n).map(a=>+a).sort((a,b)=>b-a):cin.slice(cid,cid+=n).map(a=>+a).sort((a,b)=>a-b);}
function nextm(h,w,a){var r=[],i=0;if(a)for(;i<h;i++)r.push(cin.slice(cid,cid+=w));else for(;i<h;i++)r.push(cin.slice(cid,cid+=w).map(a=>+a));return r;}
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill().map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill().map(x=>"+r+")";return eval(r);}
var streams=[];function print(s){streams.push(s);}

//dinic O(EV^2) capが全部1なら O(min(V^2/3,E^1/2)E)
const inf = 2e9;
class maxFlow{
  constructor(n){
    this.g = Array(n).fill().map(a=>[]);
    this.level = Array(n);
    this.itr = Array(n);
  }
  add(from,to,cap){
    const g = this.g;
    g[from].push({to:to, cap:cap, rev:g[to].length, isrev:false});
    g[to].push({to:from, cap:0, rev:g[from].length-1, isrev:true});
  }
  bfs(s){
    const level = this.level, g = this.g;
    level.fill(-1);
    var q = [];
    level[s] = 0; q.push(s);
    for(var i = 0; i < q.length; i++){
      var v = q[i];
      for(var j = 0; j < g[v].length; j++){
        var e = g[v][j];
        if(e.cap > 0 && level[e.to] < 0){
          level[e.to] = level[v] + 1;
          q.push(e.to);
        }
      }
    }
  }
  dfs(v,t,f){
    if(v === t)return f;
    const itr = this.itr, g = this.g, level = this.level;
    for(var i = itr[v]; i < g[v].length; i = ++itr[v]){
      var e = g[v][i];
      if(e.cap > 0 && level[v] < level[e.to]){
        var d = this.dfs(e.to, t, Math.min(f, e.cap));
        if(d > 0){
          e.cap -= d;
          g[e.to][e.rev].cap += d;
          return d;
        }
      }
    }
    return 0;
  }
  run(s,t){
    var r = 0, f;
    while(this.bfs(s), this.level[t] >= 0){
      this.itr.fill(0);
      while((f = this.dfs(s, t, inf)) > 0)r += f;
    }
    return r;
  }
  use(){
    const r = [], g = this.g;
    for(var i = 0; i < g.length; i++){
      for(var j = 0; j < g[i].length; j++){
        var e = g[i][j];
        if(!e.isrev || e.cap === 0)continue;
        r.push([e.to, i, e.cap]);
      }
    }
    return r;
  }
}

var myOut = main();
if(myOut !== undefined)console.log(String(myOut));
if(streams.length)console.log(streams.join("\n"));

function main(){
  var [n,m] = nexts(2);
  var s = [];
  for(var i = 0; i < n; i++){
    s.push(nextstr().split(""));
  }
  var nm = n*m,mf = new maxFlow(nm+2);
  for(var y = 0; y < n; y++){
    for(var x = y&1; x < m; x+=2){
      if(s[y][x] === "#")continue;
      var z = y*m + x + 1;
      mf.add(0,z,1);
      if(y && s[y-1][x] === ".")mf.add(z,z-m,1);
      if(x && s[y][x-1] === ".")mf.add(z,z-1,1);
      if(y < n-1 && s[y+1][x] === ".")mf.add(z,z+m,1);
      if(x < m-1 && s[y][x+1] === ".")mf.add(z,z+1,1);
    }
  }
  for(var y = 0; y < n; y++){
    for(var x = (y&1)^1; x < m; x+=2){
      if(s[y][x] === "#")continue;
      var z = y*m + x + 1;
      mf.add(z,nm+1,1);
    }
  }
  console.log(mf.run(0,nm+1));
  var a = mf.use();
  for(var i = 0; i < a.length; i++){
    var [u,v] = a[i];
    if(u === 0 || v === nm+1)continue;
    if(u > v)[u,v] = [v,u];
    u--, v--;
    var y = u/m|0, x = u % m;
    if(v-u === m){
      s[y][x] = "v", s[y+1][x] = "^";
    }else{
      s[y][x] = ">", s[y][x+1] = "<";
    }
  }
  return s.map(a=>a.join("")).join("\n");
}