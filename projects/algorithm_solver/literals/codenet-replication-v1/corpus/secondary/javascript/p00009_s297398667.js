// 標準入力
var fs = require('fs'),
length = fs.fstatSync(process.stdin.fd).size,
buffer = new Buffer(length),
bytesRead = fs.readSync(process.stdin.fd, buffer, 0, length, 0),
input = buffer.toString('utf8', 0, bytesRead).split('\n');
main();
   
// ここから
function main(){
  var primeNumbers = calcPrimeNumbers();
  for(var i = 0, len = input.length - 1; i < len; i++){
    console.log(primeNumbers[input[i] - 0]);
  }
  
    
}
  
function calcPrimeNumbers(){
  var max = 999999;
  var primeNumbers = new Int8Array(max + 1);
  
  // 除外
  primeNumbers[0] = primeNumbers[1] = 1;
  for(var i = 2, maxI = ~~Math.sqrt(max); i <= maxI; i++){
    if(primeNumbers[i]){
      continue;
    }
      
    for(var j = (i<<1); j <= max; j+=i){
      primeNumbers[j] = 1;
    }
  }
  
  var primeNums = new Int32Array(max + 1);
  var sum = 0;
  for(var i = 1; i <= max; i++){
    sum = primeNums[i] += sum + 1 - primeNumbers[i];
  }
    
  return primeNums;
}