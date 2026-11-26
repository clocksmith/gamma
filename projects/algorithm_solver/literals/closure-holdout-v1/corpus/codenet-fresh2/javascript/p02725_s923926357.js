"use strict"; // inputに入力データ全体が入る

function Main(input) {
  var lines = input.split('\n');
  var k = parseInt(lines[0].split(' ')[0]);
  var a = lines[1].split(' ').map(function (aa) {
    return parseInt(aa);
  });
  var mx = k - a[a.length - 1] + a[0];
  var sum = mx;

  for (var i = 0; i < a.length - 1; i++) {
    var b = a[i + 1] - a[i];
    sum += b;

    if (mx < b) {
      mx = b;
    }
  }

  console.log(sum - mx);
} //*この行以降は編集しないでください（標準入出力から一度に読み込み、Mainを呼び出します）


Main(require("fs").readFileSync("/dev/stdin", "utf8"));