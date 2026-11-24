function Main(input) {
  input = input.split("\n");
  var n = parseInt(input[0]);
  d1 = new Array(n).fill(n);
  d1[0]=0;
  d2 = new Array(n).fill(n);
  d2[n-1]=0;
  side = new Array(n).fill([]);
  for(i=0;i<n-1;i++){
    var a = parseInt(input[i+1].split(" ")[0])-1;
    var b = parseInt(input[i+1].split(" ")[1])-1;
    if(side[a].length==0){
    side[a]=[b];
    }else{
    side[a].push(b);
    }
    if(side[b].length==0){
      side[b]=[a];
    }else{
    side[b].push(a);
    }
  }
  queue2 = new Array();
  function f(x,d){
    queue = new Array();
    queue[0]=x;
    while(queue.length!=0){
      for(i=0;i<side[x].length;i++){
        if(d[side[x][i]]>d[x]){
          d[side[x][i]]=d[x]+1;
          queue.push(side[x][i]);
        }
      }
      queue.shift();
      x=queue[0];
    }
    return d;
  }
  d1=f(0,d1);
  d2=f(n-1,d2);
  var x=0;
  for(i=0;i<n;i++){
    if(i!=0&&i!=n-1){
      if(d1[i]<=d2[i]){
        x++;
      }
    }
  }
  var ans="Fennec";
  if(x<=n-2-x){
    ans="Snuke";
  }

  console.log('%s', ans);
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));