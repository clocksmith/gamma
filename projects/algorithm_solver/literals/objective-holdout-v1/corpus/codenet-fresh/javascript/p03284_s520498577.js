const main = function(input){
  var nums = input.trim().split(" ").map(i=>parseInt(i));
  var n = nums[0];
  var k = nums[1];
  var ans = 1;
  
  if(k<=n && n%k ===0){
  	ans = 0;
  }
  
  console.log(ans);


}


main(require("fs").readFileSync("/dev/stdin","utf-8"));