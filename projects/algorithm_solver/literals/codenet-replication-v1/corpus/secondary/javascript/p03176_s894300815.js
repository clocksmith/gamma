
function Main(input) {
  input = input.split("\n");
  var N = parseInt(input[0]);
  var h = input[1].split(" ").map(i => parseInt(i));
  var a = input[2].split(" ").map(i => parseInt(i));
  for(var i=0;N/Math.pow(2,i)>0.5;i++){
    var x = i;
  }
  var n = Math.pow(2,x);
  var dp = new Array(Math.pow(2,x)*2-1).fill(0);
  function query(a,b,k,l,r){
    if(r<=a||b<=l){
      return 0;
    }else if(a<=l&&r<=b){
      return dp[k];
    }else{
      var vl=query(a,b,k*2+1,l,(l+r)/2);
      var vr=query(a,b,k*2+2,(l+r)/2,r);
      return Math.max(vl,vr);
    }
  }
  function update(i,x){
    i+=n-1;
    dp[i]=x;
    while(i>0){
      i=Math.floor((i-1)/2);
      dp[i]=Math.max(dp[i*2+1],dp[i*2+2]);
    }
  }
  //dp[h[0]]=a[0];
  var ans=0;
  for(var i=0;i<N;i++){
    var max=0;
    max=query(0,h[i]-1,0,0,n);
    update(h[i]-1,max+a[i]);
    ans=Math.max(ans,max+a[i]);
  }
  console.log('%s', ans);
  return ans;
}
// "実行する"ボタンを押した時に実行される関数 (デバッグ用)
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
