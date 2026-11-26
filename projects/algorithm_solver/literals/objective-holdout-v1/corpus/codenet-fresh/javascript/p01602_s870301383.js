print=console.log;
ls=require("fs").readFileSync("/dev/stdin","utf-8").split("\n");ls.length--

(function (){

var cx = 0;
for (var i=1; i<ls.length; ++i) {
  n = +ls[i].split(" ")[1];
  if (ls[i][0] == "(") cx += n;
  else cx -= n;
  if (cx < 0) {
    print("NO");
    return;
  }
}
print(cx == 0 ? "YES" : "NO");
return;

})();