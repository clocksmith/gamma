function main(input) {
  var input = input.split('\n')[1].split(' ');
  var max = 0;
  var min = 10000000000;
  for (var i=0;i<input.length;i++){
  	var tmp = parseInt(input[i]);
  	if (tmp > max) {
  		max = tmp;
  	}
  	if (tmp < min) {
  		min = tmp;
  	}
   	
  }
  console.log(max - min);
}
  main(require('fs').readFileSync('/dev/stdin', 'utf8'));