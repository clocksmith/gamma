function Main(input) {
  input = input.split("\n");
  var N = parseInt(input[0].split(" ")[0]);
  var S = parseInt(input[0].split(" ")[1]);
  var A = input[1].split(" ").map(i => parseInt(i)).sort(function(a,b){return a-b});
  var mod = 998244353n;
  //var mod = 7n
  var memo = new Array(S);
  for(var i=0;i<S+1;i++){
    var memosub = [i,0n];
    memo[i]=memosub;
  }
  function modpow(a, n, mod) {
    res = 1n;
    while (n > 0) {
        if (n & 1n) res = res * a % mod;
        a = a * a % mod;
        n >>= 1n;
    }
    return res;
  }
  function modinv(a, mod) {
    return modpow(a, mod - 2n, mod);
  }
  var inv = modinv(2n,mod);
  var y = 1n;
  for(var i=0;i<N-1;i++){
    y = (y * 2n)%mod;
  }
  memo[0] = [0,1n];
  var ans = 0n;
  for(var i=0;i<N;i++){
    for(var j=memo.length-1;j>=0;j--){
      if(memo[j][0]+A[i]<=S&&j==0){
        memo[j+A[i]][1]=(memo[j+A[i]][1]+y)%mod;
      }else if(memo[j][0]+A[i]<=S){
        memo[j+A[i]][1]=(memo[j+A[i]][1]+(memo[j][1]*inv)%mod)%mod;
      }
    }
  }
  var ans = memo[memo.length-1][1].toString();
  console.log('%s', ans);
  return ans;
}

function debug(n){
  var input = document.getElementById("input"+n).value;
  var ans=Main(input);
  var result="WA";
  if(ans==document.getElementById("output"+n).value.split("\n")[0]){
    result="AC";
  }
  document.getElementById("result"+n).innerHTML=result;
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));