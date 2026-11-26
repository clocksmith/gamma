

function Main(input) {
  input = input.split("\n");
  var N = parseInt(input[0]);
  var s = new Array(N);
  var a=0;
  var b=0;
  var c=0;
  var ba=0;
  var ans=0;
  for(var i=0;i<N;i++){
    s[i]=input[i+1].split("");
    for(var j=0;j<s[i].length;j++){
      if(j==0&&s[i][j]=="B"){
        b++;
        c++;
      }
      if(j==s[i].length-1&&s[i][j]=="A"){
        a++;
        c++;
      }
      if(s[i][j]=="B"&&j>0){
        if(s[i][j-1]=="A"){
          ans++;
        }
      }
      if(c==2){
        ba++;
      }
    }
    c=0;
  }
  ans=ans+Math.min(a,b);
  if(b==ba&&a==ba&&ba!=0){
    ans--;
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