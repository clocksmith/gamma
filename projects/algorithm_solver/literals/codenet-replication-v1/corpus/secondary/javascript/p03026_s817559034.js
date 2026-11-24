

function Main(input) {
  input = input.split("\n");
  var N = parseInt(input[0]);
  var c = input[N].split(" ").map(i => parseInt(i));
  c.sort(function(a,b){return b-a});
  input.splice(N,input.length-N);
  input.shift();
  var e = input.map(i => i.split(" ").map(i => parseInt(i)));
  stem=1;
  var anssub=new Array(N).fill(-1);
  anssub[stem-1]=0;
  var queue=[stem];
  var num=1;
  while(queue.length!=0){
    for(var i=0;i<N-1;i++){
      if(e[i][0]==queue[0]){
        if(anssub[e[i][1]-1]==-1){
          anssub[e[i][1]-1]=num;
          num++;
          queue.push(e[i][1]);
        }
      }else if(e[i][1]==queue[0]){
        if(anssub[e[i][0]-1]==-1){
          anssub[e[i][0]-1]=num;
          num++;
          queue.push(e[i][0]);
        }
      }
    }
    queue.shift();
  }
  var anssub2=new Array();
  for(var i=0;i<N;i++){
    anssub2[i]=c[anssub[i]];
  }
  var ans2=[0];
  for(var i=0;i<N-1;i++){
    ans2[0]+=Math.min(anssub2[e[i][0]-1],anssub2[e[i][1]-1]);
  }
  var ans3=anssub2.join(" ");
  ans2.push(ans3);
  var ans=ans2.join("\n");

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