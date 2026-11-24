function Main(input) {
  input = input.split("\n");
  var n = parseInt(input[0].split(" ")[0]);
  var k = parseInt(input[0].split(" ")[1]);
  a = new Array();
  b = new Array();
  c = new Array();
  for(i=0;i<n;i++){
    a[i]=parseInt(input[i+1].split(" ")[0]);
    b[i]=parseInt(input[i+1].split(" ")[1]);
    c[i]=[a[i],b[i]];
  }
  c.sort(function(a,b){
    if( a[0] < b[0] ) return -1;
    if( a[0] > b[0] ) return 1;
    return 0;
  });
  s = new Array();
  var count=0;
  var ans=0;
  for(i=0;i<=n;i++){
    if(count>=k){
      ans=c[i-1][0];
      break;
    }else{
      count+=c[i][1];
    }
  }
  console.log('%s', ans);
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));