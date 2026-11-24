function Main(input) {
  input = input.split("\n");
  var x = parseInt(input[0].split(" ")[0]);
  var y = parseInt(input[0].split(" ")[1]);
  var ans = -1;
  if(x%y!=0){
    ans=x;
  }
  console.log('%s', ans);
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));