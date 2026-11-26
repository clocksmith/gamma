function main(input) {
    const args = input.split(' ');
    var n = parseInt(args[0], 10);
    const k = parseInt(args[1], 10);
  	var ans = 0;
  
	while (n > 0) {
      	n = Math.floor(n / k);
      	ans++;
    }
    console.log(ans);
}

main(require('fs').readFileSync('/dev/stdin', 'utf8'));
