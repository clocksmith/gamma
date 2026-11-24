function Main(input) {
  var vals = input.trim().split(/\s+/).map(x => parseInt(x));
  var a = vals[0];
  var b = vals[1];
  var k = vals[2];
  
  if (k < a) {
    a -= k;
  } else if (k < a + b) {
    b = b - (k - a);
    a = 0;
  } else {
    a = 0;
    b = 0;
  }
  
  console.log('%d %d', a, b);
};
 
Main(require("fs").readFileSync("/dev/stdin", "utf8"));
