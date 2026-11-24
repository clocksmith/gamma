'use strict'

function main(input){
  const lines = input.split('\n');
  const N = parseInt(lines.shift());
  const P = lines.shift().split(' ').map(x => parseFloat(x));

  const dp=[];
  for(var i =0;i<N;i++){
    dp.push(Array(N+2).fill(0.0))
  }

  dp[0][0]=P[0];
  dp[0][1]=1-P[0];

  for(var i =1;i<N;i++){
    for(var j=0;j<=i+1;j++){
      let pre_left = dp[i-1][j-1];
      if(pre_left==undefined){pre_left=0.0;}

      let pre_right = dp[i-1][j];
      if(pre_right==undefined){pre_right=0.0;}

      dp[i][j] = pre_left * (1.0 - P[i]) + pre_right * P[i]
    }
  }

  let result = 0;

  for(var i=0;i<N/2;i++){
    result += dp[N-1][i]
  }

  console.log(result);
}

main(require('fs').readFileSync('/dev/stdin', 'utf8'));
