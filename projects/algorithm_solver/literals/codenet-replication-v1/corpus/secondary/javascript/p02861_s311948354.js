function factorial(num) {
  if (num === 1) {
    return 1;
  } else {
    return num * factorial(num - 1);
  }
}

function Main(input) {
  var N = input[0].trim();
  var x = [];
  var y = [];
  for (var i = 0; i < N; i++) {
    var tmp = input[i + 1].split(" ");
    x[i] = parseInt(tmp[0], 10);
    y[i] = parseInt(tmp[1], 10);
  }

  var kyori = 0;
  for (var u = 0; u < N; u++) {
    for (var v = 0; v < N; v++) {
      if (u != v) {
        var z = Math.sqrt(
          (x[u] - x[v]) * (x[u] - x[v]) + (y[u] - y[v]) * (y[u] - y[v])
        );
        // console.log("u:%s v:%s %s", u, v, z);
        kyori += z;
      }
    }
  }

  var all = factorial(N);
//   console.log("%s", all);
//   console.log("%s", kyori);
  console.log("%s", (kyori * (all/N) )/ all);
}

Main(
  require("fs")
    .readFileSync("/dev/stdin", "utf8")
    .split("\n")
);
