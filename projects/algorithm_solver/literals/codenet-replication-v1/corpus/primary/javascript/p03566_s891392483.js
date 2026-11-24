function Main(s){
  s = s.split("\n");
  var n = +s[0];
  var t = s[1].split(" ").map(a=>+a);
  var v = s[2].split(" ").map(a=>+a);
  var l = Array(n*400+2).fill(0);
  var k = 0;
  for(var i = 0; i < n; i++){
    for(var j = 0; j < t[i]*2; j++){
      k++;
      if(l[k-1] < v[i])l[k] = l[k-1] + 0.5;
      else if(l[k-1] > v[i])l[k] = v[i];
      else l[k] = l[k-1];
    }
  }
  l[k] = 0;
  for(i = n-1; i >= 0; i--){
    for(j = 0; j < t[i]*2; j++){
      k--;
      if(l[k+1] < v[i])l[k] = Math.min(l[k+1] + 0.5, l[k]);
      else if(l[k+1] > v[i])l[k] = Math.min(v[i], l[k]);
      else l[k] = Math.min(l[k+1], l[k]);
    }
  }
  var ans = 0.125;
  for(i = 1; l[i]; i++)ans += (l[i] + l[i+1]) * 0.25;
  console.log(ans);
}
Main(require("fs").readFileSync("/dev/stdin","utf8"));