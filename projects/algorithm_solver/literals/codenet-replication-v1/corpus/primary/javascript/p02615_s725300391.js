function Main(input) {
  input = input.split("\n");
  var N = parseInt(input[0]);
  var A = input[1].split(" ").map(i => parseInt(i));
  A.sort((a,b) => b-a);
  var ans =0;
  var P = new Array(1).fill(A[0]);
  for(var i = 0;i<N-1;i++){
    ans += P[i];
    P.push(A[i+1]);
    P.push(A[i+1]);
  }

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