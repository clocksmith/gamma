/**
 * Created by hiroqn on 13/10/07.
 */
var fs = require('fs'),
    length = fs.fstatSync(process.stdin.fd).size,
    buffer = new Buffer(length),
    bytesRead = fs.readSync(process.stdin.fd, buffer, 0, length, 0),
    input = buffer.toString('utf8', 0, bytesRead).split('\n');
main();
function matrix(n, m, init) {
  var arr = [], i, j;
  for (i = 0; i < n; i++) {
    arr[i] = [];
    for (j = 0; j < m; j++) {
      arr[i][j] = init;
    }
  }
  return arr;
}

function solve(melody, phraseList) {
  var n = phraseList.length,
      dp = matrix(n + 1, melody + 1, 0),
      i, j, k,
      s, l, p,
      max;
  for (i = 0; i < n; i++) {
    s = phraseList[i][0];
    l = phraseList[i][1];
    p = phraseList[i][2];
    for (j = 0; j <= melody; j++) {
      if (s <= j) {
//        console.log(i,j)
        max = 0;
        for(k=l > j ? 0: j - l;k <= j - s; k++){
          if(max < dp[i + 1][k]){
            max = dp[i + 1][k];
          }
        }
        dp[i + 1][j] = Math.max(dp[i][j], max + p);
//        range = dp[i + 1].slice(l > j ? 0: j - l, j - s + 1);
//        dp[i + 1][j] = Math.max(dp[i][j], Math.max.apply(null, max) + p);
      } else {
        dp[i + 1][j] = dp[i][j];
      }

    }
  }
//  console.log(dp);dp[n][melody]
  return dp;
}
function main() {

  var n = input.shift() - 0,
      phraseList = [];
  for (i = 0; i < n; i++) {
    phraseList.push(input.shift().split(' ').map(Number));
  }
//  n = phraseList.length;
//  phraseList.sort(function (a, b) {
//    return a[2] - b[2];
//  });
//  console.log(phraseList)
  var m = input.shift() - 0,
      melodyList = [],
      melody,
      ans = [],
      i, j, k,
      max,
      dp,
      flag = true;
  for (i = 0; i < m; i++) {
    melodyList.push(input.shift() - 0);
  }
  dp = solve(393, phraseList);
  for (i = 0; i < m; i++) {
    melody = melodyList[i];
//    console.log(max)
    if (dp[n][melody] === 0) {
      flag = false;
    } else {
      ans.push(dp[n][melody]);
    }
  }
  if(!flag){
    console.log(-1);
    return;
  }
  ans.forEach(function(i){console.log(i)});

}