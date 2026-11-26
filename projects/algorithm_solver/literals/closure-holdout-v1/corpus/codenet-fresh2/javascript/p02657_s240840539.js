function Main(input){
    input=input.split("\n");  //ここまで必須
    var line=input[0].split(" ");
    console.log(parseInt(line[0])*parseInt(line[1]))
}
Main(require("fs").readFileSync("/dev/stdin","utf8"));
