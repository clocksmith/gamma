function Main(input) {
  input = input.split("\n");
  var N = parseInt(input[0]);
  var ans=0;
  var l = String(N).length;
  num=["3","5","7"];
  X=[3,5,7];
  var n=0;
  for(i=0;i<l-1;i++){
    var Xl=X.length;
    for(j=0;j<3;j++){
      for(k=n;k<Xl;k++){
        X.push(parseInt(num[j]+X[k]));
      }
    }
    n=Xl;
  }
  for(i=0;i<X.length;i++){
    if(X[i]>N) break;
    Xsub=String(X[i]).split("");
    if(Xsub.indexOf("3")!=-1&&Xsub.indexOf("5")!=-1&&Xsub.indexOf("7")!=-1){
      ans++;
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

