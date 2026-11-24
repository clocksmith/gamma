function Main(input) {
  input = input.split("\n");
  N = parseInt(input[0]);
  tmp = input[1].split(" ");
  a = new Array(N);
  var ans =0;
  for(i=0;i<N;i++){
    while(tmp[i]%2==0){
      ans++;
      tmp[i]/=2;
    }
  }

  console.log('%s', ans);
}
  
// "実行する"ボタンを押した時に実行される関数 (デバッグ用)
function debug(){
  var input = document.getElementById("input").value;
  Main(input);
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));
