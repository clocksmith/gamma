function Main(s){
  s = s.split("\n");
  s[0] = s[0].split(" ").map(a=>+a);
  var n = s[0][0];
  var m = s[0][1];
  var p = s[1].split(" ").map(a=>+a);
  var x = [], y = [];
  for(i = 0; i < m; i++){
    x[i] = s[i+2].split(" ").map(a=>+a);
    y[i] = x[i][1];
    x[i] = x[i][0];
  }
  var g = group(x,y,n);
  var ans = 0;
  for(i = 0; i < n; i++){
    if(g[i+1] === g[p[i]])ans++;
  }
  console.log(ans);
}
function group(a,b,n){
  var p = Array(n+1).fill(0).map(a=>[]);
  var q = Array(n+1);
  var al = a.length;
  for(var i = 0; i < al; i++){
    p[a[i]].push(b[i]);
    p[b[i]].push(a[i]);
  }
  var k = 1;
  for(i = 0; i <= n; i++){
    if(q[i])continue;
    q[i] = k;
    a = p[i];
    while(a.length){
      b = a.pop();
      if(q[b])continue;
      q[b] = k;
      for(var j = 0; j < p[b].length; j++){
        a.push(p[b][j]);
      }
    }
    k++;
  }
  return q;
}
Main(require("fs").readFileSync("/dev/stdin","utf8"));