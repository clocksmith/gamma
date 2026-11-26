function Main(s) {
  s = s.split("\n");
  const n = +s[0];
  var ans = 0;
  var m = 1e10;
  for(var i = 0; i < n; i++){
    var a = s[i+1].split(" ").map(a => +a);
    if(a[0] > a[1])m = Math.min(m, a[1]);
    ans += a[0];
  }
  if(m === 1e10)ans = 0;
  else ans -= m;
  console.log(ans);
}
Main(require("fs").readFileSync("/dev/stdin","utf8"));