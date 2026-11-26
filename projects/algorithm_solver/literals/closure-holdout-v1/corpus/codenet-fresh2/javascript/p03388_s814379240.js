function Main(s) {
  s = s.split("\n");
  const q = +s[0];
  for(var i = 0; i < q; i++){
    var a = s[i+1].split(" ").map(a => +a);
    var b = Math.max(a[0], a[1]);
    a = Math.min(a[0], a[1]);
    var c = sqrt64(kakeru32(a,b));
    var d = c[1];
    c = c[0];
    var ans = c * 2;
    if(a === b)ans -= 2;
    else if(d === 0)ans -= 3;
    else if(c * (c + 1) < a * b)ans--;
    else ans -= 2;
    console.log(ans);
  }
}
function sqrt64(a){
  const al = a.length;
  var b, c;
  if(al & 1)b = +a[0];else b = +(a[0]+a[1]);
  c = Math.sqrt(b)|0;
  b -= c * c;
  var d = c;
  for(var i = 2 - (al & 1); i < al ; i += 2){
    d = (d + d % 10) * 10;
    b = +(b + a[i] + a[i+1]);
    for(var j = 1; j <= 9; j++){
      if(b - (d + j) * j < 0) break;
    }
    c = c * 10 + --j;
    b -= (d + j) * j;
    d += j;
  }
  return [c,b];
}
function kakeru32(a,b){
	var c = a % 1e5 * b;
	var d = Math.floor(a / 1e5) * b + Math.floor(c / 1e5);
	c %= 1e5;
	if(d > 0)c = ("00000" + c).slice(-5);
	else d = "";
	return d + c;
}
Main(require("fs").readFileSync("/dev/stdin","utf8"));