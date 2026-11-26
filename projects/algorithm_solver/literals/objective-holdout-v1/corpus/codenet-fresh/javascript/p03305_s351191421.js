function Main(s){
  s = s.split("\n");
  var n = s[0].split(" ").map(a=>+a);
  var m = n[1];
  var q = n[2] - 1;
  var t = n[3] - 1;
  n = n[0];
  var u = [], v = [], a = [], b = [];
  for(var i = 0; i < m; i++){
    var z = s[i+1].split(" ").map(a=>+a);
    u[i] = z[0] - 1; v[i] = z[1] - 1; a[i] = z[2]; b[i] = z[3];
  }
  var c = dijkstra(u,v,a,q,n);
  var d = dijkstra(u,v,b,t,n);
  var e = [];
  i = n - 1;
  e[i] = 1e15 - c[i] - d[i];
  for(;i--;)e[i] = Math.max(e[i+1], 1e15 - c[i] - d[i]);
  console.log(e.join("\n"));
}
function dijkstra(a,b,c,s,k){
  var t = Array(k).fill(0).map(a=>[]);
  for(var i = 0; i < a.length; i++)t[a[i]][b[i]] = t[b[i]][a[i]] = c[i];
  var r = Array(k).fill(9e99); r[s] = 0;
  var f = Array(k).fill(0);
  var pq = new PriorityQueue();
  pq.push([s,0]);
  while(pq.size()){
    var x = pq.pop();
    if(f[x])continue;
    f[x] = 1;
    for(i in t[x]){
      if(r[i] <= r[x] + t[x][i])continue;
      r[i] = r[x] + t[x][i];
      pq.push([i,r[i]]);
    }
  }
  return r;
}
var PriorityQueue = function() {
  this.heap = new Array();
  this.pointer = 0;
};
PriorityQueue.prototype = {
  push : function(x) {
    var i = this.pointer++;
    while (i > 0) {
      //親ノードの番号を求める
      var p = Math.floor((i - 1) / 2);
      //もう逆転してなければ処理を打ち切る
      if (this.heap[p][1] <= x[1]) break;
      this.heap[i] = this.heap[p];
      i = p;
    }
    this.heap[i] = x;
  },
  pop : function() {
    var ret = this.heap[0];
    var x = this.heap[--this.pointer];
    var i = 0;
    //子ノードがなくなるまでループ
    while (i * 2 + 1 < this.pointer) {
      var a = i * 2 + 1; //左子ノード
      var b = i * 2 + 2; //右子ノード
      if (b < this.pointer && this.heap[b][1] < this.heap[a][1]) a = b;
      //もう逆転してなければ処理を打ち切る
      if (this.heap[a][1] >= x[1]) break;
      this.heap[i] = this.heap[a];
      i = a;
    }
    this.heap[i] = x;
    //最終ノードを削除する
    this.heap.pop();
    return ret[0];
  },
  size : function() {
    return this.heap.length;
  }
};
Main(require("fs").readFileSync("/dev/stdin","utf8"));