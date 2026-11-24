var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}
var priorityQueue=(function(){
  var h;
  function f(){return new PriorityQueue();}
  function PriorityQueue(){
    h=this.heap=[];
  }
  PriorityQueue.prototype.push=function(x){
    var i=h.length++,j;
    while(i){
      j=i-1>>1;
      if(h[j][0]<=x[0])break;
      h[i]=h[j],i=j;
    }
    h[i]=x;
  };
  PriorityQueue.prototype.pop=function(){
    var r=h[0],x=h.pop(),l=h.length,i=0,j;
    if(l===0)return r;
    var k=l>>1;l--;
    while(i<k){
      j=(i<<1)+1;
      if(j<l&&h[j+1][0]<h[j][0])j++;
      if(x[0]<=h[j][0])break;
      h[i]=h[j],i=j;
    }
    h[i]=x;
    return r;
  };
  return f;
})();
var MinCostFlow=(function(){
  var e,INF=1e15;
  function f(n){return new PrimalDual(n);}
  function PrimalDual(n){
    e=this.edge=Array(n).fill(0).map(a=>[]);
  }
  
  PrimalDual.prototype.add=function(from,to,cap,cost){
    e[from].push([to,cap,cost,e[to].length]);
    e[to].push([from,0,-cost,e[from].length-1]);
  }
  
  PrimalDual.prototype.minCostFlow=function(start,goal,flow){
    var s=start,g=goal,f=flow;
    var v=e.length,r=0,pq=priorityQueue();
    var potential=Array(v).fill(0);
    var preve=Array(v).fill(-1);
    var prevv=Array(v).fill(-1);
    while(f){
      var minCost=Array(v).fill(INF);
      minCost[s]=0;
      pq.push([0,s]);
      while(pq.heap.length){
        var p=pq.pop();
        if(minCost[p[1]]<p[0])continue;
        for(var i=0;i<e[p[1]].length;i++){
          var ei=e[p[1]][i];
          if(ei[1]<=0)continue;
          var nextCost=minCost[p[1]]+ei[2]+potential[p[1]]-potential[ei[0]];
          if(nextCost<minCost[ei[0]]){
            minCost[ei[0]]=nextCost;
            prevv[ei[0]]=p[1],preve[ei[0]]=i;
            pq.push([nextCost,ei[0]]);
          }
        }
      }
      if(minCost[g]===INF)return -1;
      for(var i=0;i<v;i++)potential[i]+=minCost[i];
      var addFlow=f;
      for(var i=g;i!==s;i=prevv[i]){
        if(e[prevv[i]][preve[i]][1]<addFlow)addFlow=e[prevv[i]][preve[i]][1];
      }
      f-=addFlow;
      r+=addFlow*potential[g];
      for(var i=g;i!=s;i=prevv[i]){
        var ei=e[prevv[i]][preve[i]];
        ei[1]-=addFlow;
        e[i][ei[3]][1]+=addFlow;
      }
    }
    return r;
  }
  return f;
})();

console.log(main());
function main(){
  var n = o.a();
  var flow = MinCostFlow(n*2+6);
  var s = 0;
  for(var i = 0; i < n; i++){
    var t = o.l(), x = t[0], y = t[1], c = t[2];
    s += c;
    flow.add(0,i+1,c,0);
    flow.add(i+1,n+1,1e4,x+y);
    flow.add(i+1,n+2,1e4,x-y);
    flow.add(i+1,n+3,1e4,-x+y);
    flow.add(i+1,n+4,1e4,-x-y);
  }
  for(var i = 0; i < n; i++){
    var t = o.l(), x = t[0], y = t[1], c = t[2];
    flow.add(n+i+5,2*n+5,c,0);
    flow.add(n+1,n+i+5,1e4,-x-y);
    flow.add(n+2,n+i+5,1e4,-x+y);
    flow.add(n+3,n+i+5,1e4,x-y);
    flow.add(n+4,n+i+5,1e4,x+y);
  }
  return -flow.minCostFlow(0,2*n+5,s);
}