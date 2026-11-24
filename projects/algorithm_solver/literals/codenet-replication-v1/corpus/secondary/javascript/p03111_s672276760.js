function main(input) {
  var inputs = input.split("\n");
  var N = Number(inputs[0].split(" ")[0]);
  var A = Number(inputs[0].split(" ")[1]);
  var B = Number(inputs[0].split(" ")[2]);
  var C = Number(inputs[0].split(" ")[3]);

  var sticks = inputs.filter((v,i)=>i>0).map(v=>Number(v));

  var ans = Number.MAX_VALUE;
  var patterns = rekkyo(N);
  for(var i=0;i<patterns.length;i++){
    var pattern = patterns[i];
    if(pattern.indexOf("1")>=0 && pattern.indexOf("2")>=0 && pattern.indexOf("0")>=0)
      ans = Math.min(ans, calc(sticks, pattern, [A,B,C], ans));
  }
  console.log(ans);
}

function rekkyo(n){
  var arr = [];
  var mask = "";
  for(var i=0;i<n;i++) mask += "0";
  for(var i=0;i<Math.pow(4, n);i++){
    arr.push((mask+i.toString(4)).slice(-n));
  }
  return arr;
}
function calc(sticks, pattern, ansSet, min){
  var ans = 0;
  var Lens = [0,0,0,0]; // A,B,C,使わない
  for(var i=0;i<pattern.length;i++){
    if(pattern[i]-0<3 && Lens[pattern[i]-0]>0) ans += 10;
    if(pattern[i]-0<3) Lens[pattern[i]-0] += sticks[i];
    if(min<ans) return ans;
  }
  if(min<ans) return ans;
  for(var i=0;i<ansSet.length;i++){
    ans += Math.abs(ansSet[i]-Lens[i]);
    if(min<ans) return ans;
  }
  return ans;
}

main(require('fs').readFileSync('/dev/stdin', 'utf8'))