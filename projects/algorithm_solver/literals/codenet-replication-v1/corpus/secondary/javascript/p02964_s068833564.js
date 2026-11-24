var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}
function lower_bound(d,a,b,e){for(var c;1<b-a;)d[c=0|(a+b)/2]<e?a=c:b=c;return d[a]<e?b:a};

main();
function main(){
  var n = o.a();
  var k = o.a();
  var a = o.l();
  var map = {};
  for(var i = 0; i < n; i++){
    if(map[a[i]])map[a[i]].push(i);
    else map[a[i]] = [i];
  }
  var ans;
  var u = solve2(0);
  if(k === 1 || u === -1){
    printf(solve(0));
    return;
  }
  var first = [,u];
  for(var i = 1; i < k; i++){
    var t = first[i];
    var l = lower_bound(map[t],0,map[t].length,0);
    var u = solve2(map[t][l]+1);
    if(u === -1)break;
    first.push(u);
  }
  if(u === -1)i++;
  var q = k%i;
  if(q===0){
    if(u === -1)return;
    var t = first[i-1];
    var l = lower_bound(map[t],0,map[t].length,0);
    printf(solve(map[t][l]+1));
    return;
  }
  if(q === 1)var l = 0;else{
    var t = first[q-1];
    var l = lower_bound(map[t],0,map[t].length,0);
    l = map[t][l]+1;
  }
  printf(solve(l));

  function solve(i){
    ans = [];
    for(var j = i; j < n; j++){
      var t = a[j];
      var l = lower_bound(map[t],0,map[t].length,j+1);
      if(l !== map[t].length){
        j = map[t][l];
      }else{
        ans.push(t);
      }
    }
    return ans;
  }
  function solve2(i){
    for(var j = i; j < n; j++){
      var t = a[j];
      var l = lower_bound(map[t],0,map[t].length,j+1);
      if(l !== map[t].length){
        j = map[t][l];
      }else{
        return t;
      }
    }
    return -1;
  }
}
function printf(ar){
  if(ar.length)console.log(ar.join(" "));
}