function Main(input) {
    var input = input.split(' ').map(n => parseInt(n, 10));
    var count = 0;
    var x = input[0];
    var y = input[1];
    var z = input[2];
    var i = y + 2*z;
    while(x >= i) {
        count++;
        i += y + z;
    }
    console.log(count);
    
    }
Main(require('fs').readFileSync('/dev/stdin', 'utf8'));