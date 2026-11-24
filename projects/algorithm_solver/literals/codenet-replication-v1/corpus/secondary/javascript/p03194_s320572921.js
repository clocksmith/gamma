function main(input){
  var line1 = input[0].split(' ');
  var n = parseInt(line1[0]);
  var p = parseInt(line1[1]);

  var ans = 1;
  var arr = primeFactorization(p);
  for (var i=0; i<arr.length; i++){
    var r = arr[i].r;
    while (n<=r) {
      ans *= arr[i].num;
      r=r-n;
    }
  }

  console.log(ans);
}


function parse(line){
  var ret = [];
  var arr = line.split(' ');
  for (var i = 0; i < arr.length; i++) {
    ret.push(parseInt(arr[i]));
  }
  return ret;
}

function primeFactorization(n) {
  var s = Math.floor(Math.sqrt(n));
  var r = 0;
  
  var result = [];
  for (var i = 2;i <= s;i++) {
    if ((n % i) == 0) {
      r = 0;
      do {
	r++;
	n = n / i;
      } while ((n % i) == 0);
      result.push({num:i, r:r});
    }
  }
  if (n > s) {
    result.push({num:n, r:1});
  }
  
  return result;
}

var input = '';

process.stdin.resume();
process.stdin.setEncoding('utf8');
process.stdin.on('data', function(chunk) {
  input += chunk;
});
process.stdin.on('end', function() {
  input = input.split('\n');
  main(input);
});
