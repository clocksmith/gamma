function Main(s){
  s = s.split("\n");
  var n = +s[0];
  var m = 1 << n;
  var a = s[1].split(" ").map(a=>+a);
  var b = [a[0]], c = [[a[0],0]], d = [[-1,-1]];
  for(var i = 1; i < m; i++){
    f(i);
  }
  console.log(b.slice(1).join("\n"));
  
  function f(n){
    var q = {}, s = [[a[n],n],[-1,-1]];
    for(var i = 1; i <= n; i <<= 1){
      var u = n & (i ^ 0xFFFFF);
      if(u === n)continue;
      if(s[1][0] > c[u][0])continue;
      if(s[0][1] !== c[u][1] && s[1][1] !== c[u][1]){
        if(s[0][0] <= c[u][0]){s[1] = [s[0][0],s[0][1]]; s[0] = c[u];}
        else s[1] = c[u];
      }
      if(s[1][0] <= d[u][0] && s[0][1] !== d[u][1] && s[1][1] !== d[u][1]){
        if(s[0][0] > d[u][0])s[1] = d[u];
        else {s[1] = [s[0][0],s[0][1]]; s[0] = d[u];}
      }
    }
    c[n] = s[0];
    d[n] = s[1];
    b[n] = Math.max(b[n-1], c[n][0] + d[n][0]);
  }
}
Main(require("fs").readFileSync("/dev/stdin","utf8"));