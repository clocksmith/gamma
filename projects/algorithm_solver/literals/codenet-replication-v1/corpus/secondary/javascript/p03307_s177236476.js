function Main(input) {
	input = parseInt(input.trim());
  if(input % 2 == 0){
     console.log(input);
     }else{
       console.log(input * 2);
     }
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));
