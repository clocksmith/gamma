function Main(input) {
    input = input.trim().split('');
    sum = input.length-2;
    console.log(input[0] + sum + input[input.length-1]);
    
    }
Main(require('fs').readFileSync('/dev/stdin', 'utf8'));