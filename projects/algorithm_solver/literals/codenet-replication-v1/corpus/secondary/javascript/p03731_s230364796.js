function Main(input){
  var N = input.split("\n")[0].split(" ")[0];
  var T = input.split("\n")[0].split(" ")[1];
  N = parseInt(N,10);
  T = parseInt(T,10);
  var t =input.split("\n")[1].split(" ");

  var jud;
  var count = 0;
  for(i=0;i<N;i++){
    t[i] = parseInt(t[i],10);
    if(i===0){
      jud = t[i] >= T;
    }else{
      jud = (t[i]-t[i-1]) >= T;
    }
    if(jud===true){
      count += T;
    }else{
      if(i===0){
        count += t[i];
      }else{
        count += (t[i]-t[i-1]);
      }
    }
  }
  count += T;
  console.log(count);
}
 
Main(require("fs").readFileSync("/dev/stdin", "utf8"));


