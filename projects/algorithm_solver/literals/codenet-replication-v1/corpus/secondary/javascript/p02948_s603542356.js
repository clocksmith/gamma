var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}
function PriorityQueue(n){
  this.heap=Array(n||1e5);
  this.size=0;
}
PriorityQueue.prototype = {
  push:function(x){
    var h=this.heap,i=this.size++,j;
    while(i){
      j=i-1>>1;
      if(h[j]<=x)break;
      h[i]=h[j],i=j;
    }
    h[i]=x;
  },
  pop:function(){
    var h=this.heap,s=this.size-1,x=h[s];h[s]=undefined;
    if(s<1)if(s)return;else return --this.size,x;
    var r=h[0],i=0,k=s>>1,j;--this.size;
    while(i<k){
      j=(i<<1)+1;
      if(h[j+1]<h[j])++j;
      if(x<=h[j])break;
      h[i]=h[j],i=j;
    }
    return h[i]=x,r;
  },
  top:function(){return this.heap[0];},
};

console.log(main());
function main(){
  var n = o.a();
  var m = o.a();
  var a = o.m(n);
  a.push([1e9,0]);
  a.sort((a,b)=>a[0]-b[0]);
  var ans = 0, j = 0;
  var pq = new PriorityQueue();
  for(var i = 1; i <= m; i++){
    while(a[j][0] <= i){
      pq.push(-a[j++][1]);
    }
    if(pq.size)ans -= pq.pop();
  }
  return ans;
}