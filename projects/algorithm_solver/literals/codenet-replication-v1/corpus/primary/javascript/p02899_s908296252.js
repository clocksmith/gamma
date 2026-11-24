function Main(input){
  var N = input.split('\n')[0].trim();
  var A = input.split('\n')[1].split(' ');
  N = parseInt(N,10);
  var a = [];

  

  
  for(i=0;i<N;i++){
    A[i] = parseInt(A[i],10);
    a[(A[i]-1)] = i+1;
  }
/*
  for(i=0;i<N;i++){
    Nn[i] = (i+1);
    a[i] = A.indexOf(Nn[i]);
    a[i] = parseInt(a[i],10) + 1;
  }
  */
  console.log(a.join(' '));


}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));