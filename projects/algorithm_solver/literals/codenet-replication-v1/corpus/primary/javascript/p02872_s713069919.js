"use strict";
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}

var leng = 0, nextV = 0, day = 0, takeday = -1;
var score = 0;

const INF = 1e9;
var V; //200-400
var E; //1.5V-2V
var dist;
var directDist;
var e;
var f;
var tmax; //10000
var tmax2;
const has = new Set();
var orderTime = xArray("[]",V);
const item = [];
const out = [];

var cx = 0;
function next(){return +item[cx++];}

function deliver(){
  if(has.size === 0){
    if(nextV === 0)return -2;
    return minPath(0);
  }
  var maxid = -1, max = 0;
  for(var v of has){
    if(max < orderTime[v].length)
    if(dist[nextV][v] <= tmax-day){
      maxid = v, max = orderTime[v].length;
    }
  }
  if(maxid === -1)return -2;
  return minPath(maxid);
}

function minPath(to){
  for(var v of e[nextV]){
    if(dist[nextV][to] === directDist[nextV][v]+dist[v][to]){
      leng = dist[nextV][v]-1;
      return nextV = v;
    }
  }
  return -2;
}

function solve(){
  if(leng){
    leng--;
    return nextV;
  }
  if(nextV === 0)take();
  else give();
  return deliver();
}

function take(){
  while(takeday < day){
    takeday++;
    var n = next();
    for(var i = 0; i < n; i++){
      var id = next()-1, d = next()-1;
      has.add(d);
      orderTime[d].push(takeday);
    }
  }
}

function give(){
  has.delete(nextV);
  while(orderTime[nextV].length){
    var t = day - orderTime[nextV].pop();
    score += tmax2 - t*t;
  }
}

const rl=require("readline").createInterface(process.stdin,process.stdout);
const g=(function*(){
  const gets=()=>rl.once("line",s=>g.next(s));
  var V = yield gets();
  V = V.split(" "); E = +V[1], V = +V[0];
  dist = xArray(INF,V,V);
  directDist = xArray(INF,V,V);
  e = xArray("[]",V);
  for(var i = 0; i < V; i++)dist[i][i] = 0;
  for(var i = 0; i < E; i++){
    var t = (yield gets()).split(" ");
    var v1 = t[0]-1, v2 = t[1]-1, d = +t[2];
    dist[v1][v2] = dist[v2][v1] = directDist[v1][v2] = directDist[v2][v1] = d;
    e[v1].push(v2);
    e[v2].push(v1);
  }
  for(var k = 0; k < V; k++)
  for(var i = 0; i < V; i++)
  for(var j = 0; j < V; j++){
    if(dist[i][k]+dist[k][j]<dist[i][j])dist[i][j]=dist[i][k]+dist[k][j];
  }
  f = (yield gets()).split(" ").map(a=>+a);
  tmax = +(yield gets()); //10000
  tmax2 = tmax*tmax;
  orderTime = xArray("[]",V);

  for(; day < tmax; day++){
    var t = +(yield gets());
    item.push(t);
    for(var i = 0; i < t; i++){
      var u = (yield gets()).split(" ").map(a=>+a);
      item.push(u[0],u[1]);
    }
    t = +(yield gets());
    for(var i = 0; i < t; i++){
      var u = yield gets();
    }

    out[day] = solve()+1;
    console.log(out[day]);

    t = yield gets();
    if(t[0] !== "O")return;
    t = +(yield gets());
    for(var i = 0; i < t; i++){
      var u = yield gets();
    }
  }
})();
g.next();