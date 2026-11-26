function Main(input) {
  var L = parseInt(input.split(" ")[0]);
  var R = parseInt(input.split(" ")[1]);
  var min = 2019;
  if((R - L) >= 2019){
     console.log(0);
    	return;
     }
  L = L % 2019;
  R = R % 2019;
  for(var i = L; i < R; i++){
    if(i % 2019 == 0){
       console.log(0);
    	return;
    }
    for(var j = i + 1; j <= R; j++){
      if(j % 2019 == 0){
         console.log(0);
    	return;
         }
      var cal = (i * j) % 2019;
      if(min > cal){
         min = cal;
        if(min == 0){
           console.log(min);
          return;
           }
      }
    }
  }
  console.log(min);
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));
