function main(){
  var
  i, j, k, n,
  seq, max, sum;
  for(i = 0; n = parseInt(input[i++],10); ){
    seq = [];
    for(j = 0; j < n; j++){
      seq[j] = parseInt(input[i + j],10);
    }
    i += n;
    max = -Infinity;
    for(j = 0; j < n; j++) {
      sum = 0;
      for(k = j; k < n; k++) {
        sum += seq[k];
        if(sum > max) max = sum;
      }
    }
    console.log(max);
  }
}

var
input = '';

process.stdin.resume();
process.stdin.setEncoding('utf8');
process.stdin.on('data', function(chunk) {
  input += chunk;
});
process.stdin.on('end', function() {
  input = input.split('\n');
  main();
});