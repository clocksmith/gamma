function main(input){
  input = parseInt(input);
  let answer = "";
  if(input<30){
    answer = "No";
  }else{
    answer = "Yes";
  }
  console.log(answer);
}
main(require("fs").readFileSync("/dev/stdin", "utf8"));