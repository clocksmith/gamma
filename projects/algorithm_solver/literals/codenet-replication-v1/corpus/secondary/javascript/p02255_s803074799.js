function main(input) {
  input = input.split("\n");
  var N = parseInt(input[0]);
  var values = input[1].split(" ").map(function(v) { return parseInt(v); });
  insertionSort(values);
}

function insertionSort(a) {
  for (var i = 0; i < a.length; i++) {
    for (var j = i-1; j >= 0; j--) {
      if (a[j+1] < a[j]) {
        var v  = a[j];
        a[j]   = a[j+1];
        a[j+1] = v;
      }
    }
    console.log(a.join(' '));
  }
}
main(require("fs").readFileSync("/dev/stdin", "utf8"));