function Main(input) {
    var lines = input.split("\n");
    var N = parseInt(lines[0]);
    var a = lines[1].split(" ").map(function(i) { return parseInt(i);});
    var sortedA = a.slice().sort(function(a,b) { return a - b;});
    var med1 = sortedA[N/2-1];
    var med2 = sortedA[N/2];
    a.forEach(function(i) {console.log(i<=med1 ? med2 : med1);})
}
 
Main(require('fs').readFileSync('/dev/stdin', 'utf8'));