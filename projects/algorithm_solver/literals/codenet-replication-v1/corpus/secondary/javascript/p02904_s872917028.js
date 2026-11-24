var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}
function PriorityQueue(){
  this.heap = [];
}
PriorityQueue.prototype = {
  push : function(x){
    var h = this.heap, i = h.length++, j;
    while(i){
      j = i-1 >> 1;
      if(h[j] <= x)break;
      h[i] = h[j];
      i = j;
    }
    h[i] = x;
  },
  pop : function(){
    var h = this.heap, r = h[0], x = h.pop();
    var i = 0, k = h.length >> 1, j;
    while (i < k) {
      j = (i << 1) + 1;
      if(h[j+1] < h[j])++j;
      if(x <= h[j])break;
      h[i] = h[j];
      i = j;
    }
    if(h.length)h[i] = x;
    return r;
  },
  size : function(){return this.heap.length;},
  top : function(){return this.heap[0];},
};

console.log(main());
function main(){
  var n = o.a();
  var k = o.a();
  var p = o.l();
  var pqu = new PriorityQueue();
  var pqd = new PriorityQueue();
  var set = new Set();
  var ans = 1, id = 1, mx = p[0], f = 0;
  for(var i = 1; i < n; i++){
    if(mx < p[i])id++;
    else{
      if(id >= k){
        if(f)ans--;
        f = 1;
      }
      id = 1;
    }
    mx = p[i];
  }
  if(id >= k && f)ans--;
  for(var i = 0; i < k; i++){
    pqu.push(-p[i]);
    pqd.push(p[i]);
  }
  for(;i<n;i++){
    var t = 0;
    if(pqd.top() === p[i-k]){
      t++;
      pqd.pop();
    }
    if(pqu.top() === -p[i-k]){
      pqu.pop();
    }
    while(set.has(pqd.top()))pqd.pop();
    while(set.has(-pqu.top()))pqu.pop();
    if(pqu.top() > -p[i])t++;
    if(t < 2)ans++;
    pqd.push(p[i]);
    pqu.push(-p[i]);
    set.add(p[i-k]);
  }
  return ans;
}