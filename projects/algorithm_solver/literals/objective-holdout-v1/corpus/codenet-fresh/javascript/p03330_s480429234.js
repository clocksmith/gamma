'use strict'
function Main(input){
  input=input.split(/\s+/);
  for(let i=0;i<input.length;i++)
    input[i]=parseInt(input[i]);
  var N=input.shift();
  var C=input.shift();
  var D=[];
  for(let i=0;i<C;i++){
    D[i]=[];
    for(let j=0;j<C;j++)
      D[i][j]=input[C*i+j];
  }
  var c=[];
  for(let i=0;i<N;i++){
    c[i]=[];
    for(let j=0;j<N;j++)
      c[i][j]=input[C*C+N*i+j]-1;
  }
  var group=[[],[],[],];//各グループの各色の数を納めた配列
  for(let i=0;i<3;i++)
    for(let j=0;j<C;j++)
      group[i][j]=0;
  for(let i=0;i<N;i++)
    for(let j=0;j<N;j++)
      group[(i+j)%3][c[i][j]]++;
  var cost=[[],[],[]];//cost[i][j]でgroup[i]を色jに揃える違和感
  for(let i=0;i<3;i++)
    for(let j=0;j<C;j++){
      cost[i][j]=0;
      for(let k=0;k<C;k++){
        cost[i][j]+=group[i][k]*D[k][j];
      }
    }
  var bestColors=[[],[],[],];//各groupのbest3を出して全探索
  var bestScores=[[],[],[],];//bestColorsに対応するScore
  for(let i=0;i<3;i++)
    for(let j=0;j<3;j++){
      bestScores[i][j]=Math.min.apply(null,cost[i]);
      bestColors[i][j]=cost[i].indexOf(bestScores[i][j]);
      cost[i][bestColors[i][j]]=Infinity;
    }
  var candidates=[];
  var score=[];
  var color=[];
  for(let i=0;i<3;i++){
    color[0]=bestColors[0][i]
    score[0]=bestScores[0][i];
    for(let j=0;j<3;j++){
      color[1]=bestColors[1][j];
      if(color[0]===color[1])continue;
      score[1]=bestScores[1][j];
      for(let k=0;k<3;k++){
        color[2]=bestColors[2][k];
        if(color[0]===color[2]||color[1]===color[2])continue;
        score[2]=bestScores[2][k];
        candidates.push(score[0]+score[1]+score[2]);
      }
    }
  }
  var min=Math.min.apply(null,candidates);
  console.log(min);
}

var fs=require('fs');
var I=fs.readFileSync('/dev/stdin','utf8');
Main(I);