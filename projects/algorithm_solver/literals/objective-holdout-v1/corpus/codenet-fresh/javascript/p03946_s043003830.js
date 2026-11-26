function Main(input) {
  input = input.split("\n");
  tmp = input[0].split(" ");
  var n = parseInt(tmp[0]);
  tmp2 = input[1].split(" ");
  a = new Array(n);
  var max=0;
  var ans=0;
  var min=0;
  for(i=0;i<n;i++){
    a[i]=parseInt(tmp2[i]);
    if(min>a[i]||i==0){
      min=a[i];
    }
    if(max==a[i]-min){
      ans++;
    }else if(max<a[i]-min){
      ans=1;
      max=a[i]-min;
    }
  }
  console.log('%s', ans);
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));