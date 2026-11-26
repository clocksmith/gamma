'use strict';
(function(input){
  input=input.trim().split(/\s+/).map(x=>x-0);
  const N=input.shift();
  const a=input;
  const dp=new Array(N).fill(0).map((x,i)=>new Array(N-i).fill(Infinity));
  //dp[i][j]は添字jからj+iまでのslimeを合成する最小コスト。
  dp[0]=new Array(N).fill(0);
  
  const size=new Array(N).fill(0).map((x,i)=>new Array(N-i).fill(0));
  //size[i][j]は添字jからj+iまでのスライムを合成して得られるスライムのサイズ。
  size[0]=a;
  for(let i=1;i<N;i++)
    for(let j=0;j<N-i;j++)
      size[i][j]=size[i-1][j]+size[0][j+i];
  
  for(let i=1;i<N;i++){
    for(let j=0;j<N-i;j++){
      for(let k=0;k<i;k++){
        //添字jからj+kまでとj+k+1からj+iまでとをそれぞれくっつけて最後に合わせる。
        //kを0からi-1までふったときの最小を出す。
        dp[i][j]=Math.min(dp[i][j],dp[k][j]+dp[i-k-1][j+k+1]+size[k][j]+size[i-k-1][j+k+1]);
      }
    }
  }
  //console.log(size);
  //console.log(dp);
  console.log(dp[N-1][0]);
})(require('fs').readFileSync('/dev/stdin','utf8'));
