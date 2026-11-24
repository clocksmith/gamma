function Main(input) {
  input = input.split("\n");
  var n = parseInt(input[0]);
  tmp = input[1].split(" ");
  a=new Array(n).fill(0);
  for(i=0;i<n;i++){
    a[i]=parseInt(tmp[i]);
  }
  var odd=0;
  var four=0;
  for(i=0;i<n;i++){
    if(a[i]%2==1){
      odd++;
    }else if(a[i]%4==0){
      four++;
    }
  }
  var ans="No";
  if(odd==0){
    ans="Yes";
  }else if(odd-four<=0){
    ans="Yes";
  }else if(n%2==1&&odd-four<=1&&four>0){
    ans="Yes";
  }
  console.log('%s', ans);
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));