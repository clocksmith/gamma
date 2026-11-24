main = input => {
  input = input.split('\n').map(x => x.split(' ')).map(x => x.map(parseFloat));
  var N = input[0];
  var A = input[1];
  var B = input[2];
  var C = input[3];
  
  var result = 0;
  A.forEach((value,index) => {
    result += B[value - 1];
    if(index === 0){
      return true;
    }
    // 料理N食べた時に一個前に食べたものが料理N-1ならば
    if(A[index] === A[index - 1] + 1){
      result += C[value - 2];
    }
  });
  process.stdout.write(result);
}

main(require('fs').readFileSync('/dev/stdin','utf8'));