function Main(input) {
  input = input.split("\n");
  var n = parseInt(input[0]);
  tmp1=input[1].split(" ");
  tmp2=input[2].split(" ");
  tmp3=input[3].split(" ");
  a = new Array(n).fill(0);
  b = new Array(n).fill(0);
  c = new Array(n).fill(0);
  for(i=0;i<n;i++){
    a[i]=parseInt(tmp1[i]);
  }
  for(i=0;i<n;i++){
    b[i]=parseInt(tmp2[i]);
  }
  for(i=0;i<n;i++){
    c[i]=parseInt(tmp3[i]);
  }
  var ans=0;
  a.sort(function(a,b){
          if( a < b ) return -1;
          if( a > b ) return 1;
          return 0;
  });
  b.sort(function(a,b){
          if( a < b ) return -1;
          if( a > b ) return 1;
          return 0;
  });
  c.sort(function(a,b){
          if( a < b ) return -1;
          if( a > b ) return 1;
          return 0;
  });
  b1 = new Array(n).fill(0);
  b2 = new Array(n).fill(0);
  for(i=0;i<n;i++){
    if(i==0||b1[i-1]==0){
      var x=0;
    }else{
      var x=b1[i-1]-1;
    }
    for(j=x;b[i]>a[j];j++){
      b1[i]=j+1;
    }
  }
  for(i=n-1;i>=0;i--){
    if(i==n-1||b2[i+1]==0){
      var x=n-1;
    }else{
      var x=n-(b2[i+1]);
    }
    for(j=x;b[i]<c[j];j--){
      b2[i]=n-j;
    }
  }
  for(i=0;i<n;i++){
    ans=ans+b1[i]*b2[i];
  }
  console.log('%s', ans);
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));