function Main(input) {
  input = input.split("\n");
  var N = parseInt(input[0].split(" ")[0]);
  var M = parseInt(input[0].split(" ")[1]);
  C=new Array(M);
  P=new Array(0);
  for(i=0;i<M;i++){
    tmp=input[i+1].split(" ");
    Csub=[parseInt(tmp[0]),parseInt(tmp[1]),i];
    C[i]=Csub;
  }
  C.sort(function(a, b) {
    return (a[0]-b[0]||a[1]-b[1])
	});
  for(i=0;i<M;i++){
    var y="";
    c=`00000${C[i][0]}`.slice(-6);
    if(i==0){
      var cnt=1;
    }else if(C[i][0]!=C[i-1][0]){
      cnt=1;
    }else{
      cnt++;
    }
    y=`00000${cnt}`.slice(-6);
    P.push([`${c}${y}`,C[i][2]]);
  }
  P.sort((a,b)=>a[1]-b[1]);
  var ans="";
  for(i=0;i<M;i++){
    if(i!=M-1){
      ans=ans+P[i][0]+"\n";
    }else{
      ans=ans+P[i][0];
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
