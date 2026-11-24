var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}
var move = xArray("[]",6);
var set = new Set([0]);

console.log(main());
function main(){
  var n = o.a();
  for(var i = 0; i < n; i++){
    var x = o.a();
    var y = o.a();
    var d = o.a(1);
    if(d === "U"){
      solve(0,y);
      solve(5,x);
    }else if(d === "R"){
      solve(1,x);
      solve(4,y);
    }else if(d === "D"){
      solve(2,y);
      solve(5,x);
    }else{
      solve(3,x);
      solve(4,y);
    }
  }
  calc(move[0][1],move[4][1],move[2][1]);
  calc(-move[2][0],-move[4][0],-move[0][0]);
  calc(move[1][1],move[5][1],move[3][1]);
  calc(-move[3][0],-move[5][0],-move[1][0]);
  var ans = 1e18;
  for(var i of set){
    var u = max(move[0][1]+i,move[2][1]-i,move[4][1]);
    var d = min(move[0][0]+i,move[2][0]-i,move[4][0]);
    var r = max(move[1][1]+i,move[3][1]-i,move[5][1]);
    var l = min(move[1][0]+i,move[3][0]-i,move[5][0]);
    var s = (u-d)*(r-l);
    if(s < ans)ans = s;
  }
  return ans;
}

function solve(i,z){
  if(move[i].length){
    if(move[i][0] > z)move[i][0] = z;
    else if(move[i][1] < z)move[i][1] = z;
  }else{
    move[i][0] = move[i][1] = z;
  }
}

function calc(u,x,d){
  set.add(Math.max(0,(d-x)||0));
  set.add(Math.max(0,((d-u)/2)||0));
  set.add(Math.max(0,(x-u)||0));
}

function max(){
  var a = arguments;
  var r = a[0];
  for(var i = 1; i < a.length; i++){
    if(isNaN(a[i]))continue;
    if(r>a[i])continue;
    r = a[i];
  }
  return r;
}

function min(){
  var a = arguments;
  var r = a[0];
  for(var i = 1; i < a.length; i++){
    if(isNaN(a[i]))continue;
    if(r<a[i])continue;
    r = a[i];
  }
  return r;
}