function Main(input){
  input = input.split(" ");
  
  var k = parseInt(input[0],10);
  var x = parseInt(input[1],10);
  
  if(k * 500 >= x){
    console.log("Yes");
  }
  else{
    console.log("No");
  }
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));
