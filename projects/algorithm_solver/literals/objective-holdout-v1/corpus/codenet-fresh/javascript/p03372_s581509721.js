function Main(s) {
  s = s.split("\n");
  s[0] = s[0].split(" ").map(a => +a);
  const n = s[0][0];
  const c = s[0][1];
  if(n === 1){
    s[1] = s[1].split(" ").map(a => +a);
    console.log(Math.max(0, s[1][1] - s[1][0], s[1][1] - c + s[1][0]));
    return;
  }
  var x = [];
  var p = [];
  var m = [];
  var ans;
  var kp = [];
  var km = [];
  x[0] = s[1].split(" ").map(a => +a);
  p[0] = x[0][1];
  ans = Math.max(0, p[0] - x[0][0]);
  kp[0] = ans;
  for(var i = 1; i < n; i++){
    x[i] = s[i+1].split(" ").map(a => +a);
    p[i] = p[i-1] + x[i][1];
    ans = Math.max(ans, p[i] - x[i][0]);
    kp[i] = ans;
  }
  m[n-1] = x[n-1][1];
  km[n-1] = Math.max(0, m[n-1] - c + x[n-1][0]);
  ans = Math.max(ans, km[n-1]);
  for(i = n-2; i >= 0; i--){
    m[i] = m[i+1] + x[i][1];
    km[i] = Math.max(km[i+1], m[i] - c + x[i][0]);
    ans = Math.max(ans, m[i] - c + x[i][0], km[i+1] + kp[i] - x[i][0], km[i+1] + kp[i] - c + x[i+1][0]);
  }
  console.log(ans);
}
Main(require("fs").readFileSync("/dev/stdin","utf8"));