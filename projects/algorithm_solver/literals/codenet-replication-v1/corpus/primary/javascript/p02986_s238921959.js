var GET=(function(){function f(s){return new g(s);}function g(s){this._s=s.trim().split("\n");this._y=0;}g.prototype.a=function(f){var s=this._s, y=this._y, r;if(typeof s[y]==="string")s[y]=s[y].split(" ").reverse();r=s[y].pop();if(!s[y].length)this._y++;return f?r:+r;};g.prototype.l=function(f){var s=this._s[this._y++].split(" ");return f?s:s.map(a=>+a);};g.prototype.m=function(n,f){var r=this._s.slice(this._y,this._y+=n).map(a=>a.split(" "));return f?r:r.map(a=>a.map(a=>+a));};g.prototype.r=function(n,f){var r=this._s.slice(this._y,this._y+=n);return f?r:r.map(a=>+a);};return f;})();
var o=GET(require("fs").readFileSync("/dev/stdin","utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}
var Tree = (function(){
  var g,ts,dist,depth,parent,r,nlog2;
  function f(graph,root){
    g = graph, r = root;
    return new tree();
  }
  function tree(){
    var n = g.length;
    ts = this;
    dist = this.dst = Array(n).fill(0);
    depth = this.depth = Array(n).fill(0);
    nlog2 = 0;
    var t = n-1;
    while(t>>=1)nlog2++;
    parent = this.parent = Array(n).fill(0).map(a=>Array(nlog2+1).fill(r));
    dfs(r,-1);
  }
  function dfs(v,p){
    var d = depth[v];
    if(d){
      parent[v][0] = p;
      for(var i = 1; (1<<i)<=d; i++){
        parent[v][i] = parent[parent[v][i-1]][i-1];
      }
    }
    var l = g[v].to.length;
    for(var i = l; i--;){
      var V = g[v].to[i];
      if(V === p)continue;
      depth[V] = d+1;
      dist[V] = dist[v] + g[v].dist[i];
      dfs(V,v);
    }
  }
  tree.prototype.lca = function(u,v){
    if(depth[u] < depth[v]){var t = u; u = v, v = t;}
    for(var i = nlog2; depth[u] > depth[v]; i--){
      if(depth[parent[u][i]] >= depth[v])u = parent[u][i];
    }
    if(u === v)return u;
    for(i = nlog2; i--;){
      if(parent[u][i] !== parent[v][i])u = parent[u][i], v = parent[v][i];
    }
    return parent[u][0];
  };
  tree.prototype.dist = function(u,v){
    var t = this.lca(u,v);
    return dist[u] + dist[v] - 2 * dist[t];
  };
  return f;
})();

function main(){
  var n = o.a();
  var q = o.a();
  var g = xArray("{to:[],dist:[],color:[]}",n);
  for(var i = 1; i < n; i++){
    var t = o.l(), a = t[0]-1, b = t[1]-1, c = t[2], d = t[3];
    g[a].to.push(b); g[a].color.push(c); g[a].dist.push(d);
    g[b].to.push(a); g[b].color.push(c); g[b].dist.push(d);
  }
  var x = o.m(q);
  var tree = Tree(g,0);
  var cnt = xArray("{}",n);
  var sum = xArray("{}",n);
  var color = xArray("new Set()",n);
  var node = {cnt:xArray(0,n),sum:xArray(0,n)};
  for(i = 0; i < q; i++){
    x[i][2]--, x[i][3]--;
    x[i][4] = tree.lca(x[i][2],x[i][3]);
    color[x[i][2]].add(x[i][0]);
    color[x[i][3]].add(x[i][0]);
    color[x[i][4]].add(x[i][0]);
  }
  dfs(0,-1);
  var ans = Array(q);
  for(var i = 0; i < q; i++){
    ans[i] = tree.dist(x[i][2],x[i][3]);
    ans[i] += (cnt[x[i][2]][x[i][0]] + cnt[x[i][3]][x[i][0]] - 2*cnt[x[i][4]][x[i][0]]) * x[i][1];
    ans[i] -= sum[x[i][2]][x[i][0]] + sum[x[i][3]][x[i][0]] - 2*sum[x[i][4]][x[i][0]];
  }
  console.log(ans.join("\n"));

  function dfs(v,p){
    for(var i of color[v]){
      cnt[v][i] = node.cnt[i];
      sum[v][i] = node.sum[i];
    }
    var l = g[v].to.length;
    for(i = l; i--;){
      var V = g[v].to[i];
      if(V === p)continue;
      node.cnt[g[v].color[i]]++;
      node.sum[g[v].color[i]] += g[v].dist[i];
      dfs(V,v);
      node.cnt[g[v].color[i]]--;
      node.sum[g[v].color[i]] -= g[v].dist[i];
    }
  }
}
if (process.argv.length <= 2) require("child_process").fork("Main.js", ["1"], { execArgv: ["--stack-size=240000"] });
else {
  main();
}