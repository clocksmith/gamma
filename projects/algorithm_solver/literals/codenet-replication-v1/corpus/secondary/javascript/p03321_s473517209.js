function Main(s){
  s = s.split("\n");
  var n = s[0].split(" ").map(a=>+a);
  var m = n[1];
  n = n[0];
  var b = Array(n).fill(0).map(a=>Array(n).fill(1));
  for(var i = 0; i < m; i++){
    var a = s[i+1].split(" ").map(a=>a-1);
    b[a[0]][a[1]] = b[a[1]][a[0]] = 0;
  }
  var c = Array(n).fill(0);
  var z = 0;
  var x = [], y = [];
  for(i = 0; i < n; i++){
    if(c[i])continue;
    x[z] = 0;
    y[z] = 0;
    c[i] = 1;
    var a = [];
    for(var j = i+1; j < n; j++){
      if(b[i][j]){x[z] = 1; a.push(j);}
    }
    if(a.length){
      if(f(a,1)){console.log(-1); return;}
    }else x[z] = 1;
    z++;
  }
  var d = Array(n).fill(0);
  d[x[0]] = d[y[0]] = 1;
  for(i = 1; i < x.length; i++)
  for(j = n-1; j >= 0; j--){
    if(d[j]){d[j] = 0; d[j+x[i]] = 1; d[j+y[i]] = 1;}
  }
  var k = 0;
  for(i = 0; i < n; i++){
    if(d[i])k = Math.max(k, Math.min(i, n - i))
  }
  console.log(k*(k-1)/2+(n-k)*(n-k-1)/2);
  
  function f(p,q){
    if(!p.length)return;
    var a = [];
    for(var i = 0; i < p.length; i++){
      if(c[p[i]])continue;
      c[p[i]] = 1;
      if(q)y[z]++;else x[z]++;
      for(var j = i+1; j < p.length; j++){
        if(c[p[j]])continue;
        if(b[p[i]][p[j]])return 1;
      }
      for(j = 0; j < n; j++)if(b[p[i]][j])a.push(j);
    }
    if(f(a, q^1))return 1;;
  }
}
Main(require("fs").readFileSync("/dev/stdin","utf8"));