function Main(input){
  
  var a = Number(input);

  if(a < 1200) {
    console.log('ABC');
  } else {
    console.log('ARC');
  }

}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));