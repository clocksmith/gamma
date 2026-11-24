function Main(input) {
  input = input.split("\n");
  tmp = input[0].split(" ");
  var answer = 0;
  var count = 0;
  var p = new Array();
  var number = new Array();
  for(var i=22;i<Number(tmp[1])+1;i++){
    if(i%10!=1){
      number[count] = String(i).split("");
      p[count] = number[count][0]*number[count][1];
    }
    count++;
    if(i%10==1){
      count--;
    }
  }
  for(var j=0;j<p.length;j++){
    if(p[j]<=tmp[0] && p[j]!=0){
      answer++;
    }
  }
  console.log(answer);
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));