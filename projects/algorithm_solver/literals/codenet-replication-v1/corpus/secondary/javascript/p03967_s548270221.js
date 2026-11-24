function Main(input){
  input = input.split("");
  var sum = 0;
  var g=0;
  var p=0;
  input.forEach(function(val){
      switch(val){
          case "g":
              if(p<g){
                  sum++;
                  p++;
              }else{
                  g++;
              }
              break;
          case "p":
              if(p<g){
                  p++;
              }else{
                  g++;
                  sum--;
              }
      }
  });
  console.log(sum);
}Main(require("fs").readFileSync("/dev/stdin", "utf8").trim());