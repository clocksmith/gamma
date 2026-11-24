function Main(input){
    input = input.split("\n");
    var mem = input[0].split(" ").map(Number);
    var arr = input[1].split(" ").map(Number);
    arr = arr.sort(function(a,b){return a-b});
    var sum = 0;
    var max = mem[1];
    var ans = 0;
    for(var i=0;i<arr.length;i++){
      sum += arr[i];
      if(max<sum){
        break;
      }else{
        ans++;
      }
  //    console.log(sum,max,ans)
    }
    if(arrsum(arr)<max) ans--;
    console.log(ans);
  }Main(require("fs").readFileSync("/dev/stdin", "utf8").trim());
  function arrsum(arr){
      var sum = 0;
      for(var i=0;i<arr.length;i++){
          sum += arr[i];
      }
      return sum;
  }