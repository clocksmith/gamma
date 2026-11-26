"use strict";
var input=require("fs").readFileSync("/dev/stdin","utf8");
var cin=input.split(/ |\n/),cid=0;
function next(){return +cin[cid++];}
function nextstr(){return cin[cid++];}
function nextbig(){return BigInt(cin[cid++]);}
function nexts(n,a){return a?cin.slice(cid,cid+=n):cin.slice(cid,cid+=n).map(a=>+a);}
function nextm(h,w,a){var r=[],i=0;if(a)for(;i<h;i++)r.push(cin.slice(cid,cid+=w));else for(;i<h;i++)r.push(cin.slice(cid,cid+=w).map(a=>+a));return r;}
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill().map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill().map(x=>"+r+")";return eval(r);}

class priorityQueue{
  constructor(){
    this.a=[];
  }
  push(num,inc){
    const a = this.a;
    for(var i = a.length, j; i; i = j){
      j = i - 1 >> 1;
      if(a[j][0] <= num)break;
      a[i] = a[j];
    }
    a[i] = [num,inc];
  }
  pop(){
    const a = this.a, r = a[0], x = a.pop(), k = a.length >> 1;
    for(var i = 0, j; i < k; i = j){
      j = (i << 1) + 1;
      if(a[j+1] && a[j+1][0] < a[j][0])j++;
      if(x[0] <= a[j][0])break;
      a[i] = a[j];
    }
    if(a.length)a[i] = x;
    return r;
  }
  get size(){
    return this.a.length;
  }
  get top(){
    return this.a[0];
  }
}

var myOut = main();
if(myOut !== undefined)console.log(myOut);

function main(){
  var q = next();
  var div = [2n,3n,5n];
  for(var i = 0; i < q; i++){
    var n = nextbig();
    var a = [nextbig(),nextbig(),nextbig()];
    var d = nextbig();
    var pq = new priorityQueue();
    var map = new Map();
    map.set(n,0n);
    pq.push(0n,n);
    while(1){
      var [cost,now] = pq.pop();
      if(map.has(now) && map.get(now) < cost)continue;
      if(now === 1n){
        console.log((cost+d).toString());
        break;
      }
      for(var j = 0; j < 3; j++){
        var aft = now / div[j];
        if(aft === 0n){
          if(now !== 4n)continue;
          var c = 3n * d + cost;
          if(!map.has(1n) || map.get(1n) > c){
            map.set(1n,c);
            pq.push(c,1n);
          }
          now++, cost += d, aft = 1n;
        }
        var mod = now % div[j];
        var c1 = mod * d + a[j];
        var c2 = (now - aft) * d;
        if(c2 < c1)c1 = c2;
        c1 += cost;
        if(!map.has(aft) || map.get(aft) > c1){
          map.set(aft,c1);
          pq.push(c1,aft);
        }
        if(mod === 0n)continue;
        aft++;
        c1 = (div[j] - mod) * d + a[j];
        c2 = (now - aft) * d;
        if(c2 < c1)c1 = c2;
        c1 += cost;
        if(!map.has(aft) || map.get(aft) > c1){
          map.set(aft,c1);
          pq.push(c1,aft);
        }
      }
    }
  }
}