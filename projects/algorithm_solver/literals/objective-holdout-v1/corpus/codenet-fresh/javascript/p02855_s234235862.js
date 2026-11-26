"use strict";
var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}
var ans,s;

console.log(main());
function main(){
  var h = o.a();
  var w = o.a();
  var k = o.a();
  s = o.r(h,1);
  ans = xArray(1,h,w);
  solve(0,0,h,w,1,k);
  return ans.map(a=>a.join(" ")).join("\n");
}

function solve(y,x,h,w,id,k){
  if(k === 1){
    for(var y3 = y; y3 < h; y3++)
    for(var x3 = x; x3 < w; x3++){
      ans[y3][x3] = id;
    }
    return;
  }
  var y2 = xArray(0,h-y);
  var x2 = xArray(0,w-x);
  for(var y3 = y; y3 < h; y3++){
    for(var x3 = x; x3 < w; x3++){
      if(s[y3][x3] === "#"){
        y2[y3-y]++;
        x2[x3-x]++;
      }
    }
  }
  for(var y3 = y+1; y3 < h; y3++)y2[y3-y] += y2[y3-y-1];
  for(var x3 = x+1; x3 < w; x3++)x2[x3-x] += x2[x3-x-1];
  if(x + 1 === w)return f(y,x,h,w,id,k,y2);
  var xf = x+w>>1;
  xf-= x;
  if(x2[xf] === 0){
    while(++xf){
      if(x2[xf] !== 0)break;
    }
    if(x2[xf] === k)return f(y,x,h,w,id,k,y2);
  }
  if(x2[xf] === k){
    while(--xf){
      if(x2[xf] !== k)break;
    }
    if(x2[xf] === 0 || x2[xf] === k)return f(y,x,h,w,id,k,y2,k);
  }
  solve(y,x,h,xf+x+1,id,x2[xf]);
  solve(y,xf+x+1,h,w,id+x2[xf],k-x2[xf]);
}

function f(y,x,h,w,id,k,y2){
  var yf = y+h>>1;
  yf -= y;
  if(y2[yf] === 0){
    while(++yf){
      if(y2[yf] !== 0)break;
    }
  }else if(y2[yf] === k){
    while(--yf){
      if(y2[yf] !== k)break;
    }
  }
  solve(y,x,yf+y+1,w,id,y2[yf]);
  solve(yf+y+1,x,h,w,id+y2[yf],k-y2[yf]);
}