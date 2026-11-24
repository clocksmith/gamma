function main(input) {
  var inputs = input.split("\n");
  var N = Number(inputs[0]);
  var a = inputs[1].split(" ").map(v=>v-0);
  var sums = [];
  for(var i=0;i<a.length;i++){
    sums[i] = (sums[i-1]||0) + a[i];
  }
  sums.push(0);
  sums.sort((a,b)=>a-b);
  var map = {};
  for(var i=1;i<sums.length;i++){
    if(sums[i-1]==sums[i]) map[sums[i-1]] = (map[sums[i-1]]||0)+1;
  }
  var ans = 0;
  Object.keys(map).forEach(key=>{
    ans += map[key]*(map[key]+1)/2;
  });
  console.log(ans);
}

main(require('fs').readFileSync('/dev/stdin', 'utf8'))
