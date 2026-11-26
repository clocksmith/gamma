/**
 * @param {String} input
 */
function Main(input){
	var inputs = input.split("\n")[0].split(' ').map(function (num){return Number(num);});
    var a = inputs[0];
    var b = inputs[1];
    var c = inputs[2];
    var d = inputs[3];
    if(b < c || d < a) return 0;
    var longestSec = Math.max(b,d) - Math.min(a,c);
    return longestSec - Math.abs(a-c) - Math.abs(b-d);
}
console.log(Main(require("fs").readFileSync("/dev/stdin", "utf8")));