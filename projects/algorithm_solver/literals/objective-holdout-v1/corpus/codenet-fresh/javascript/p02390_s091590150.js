var S = parseInt(require('fs').readFileSync('/dev/stdin').toString());
var res = separate(S);
while (res.split(':').length < 3)
	res = '0:' + res;
console.log(res);

function separate(num) {
	if (num < 60) return String(num);
	return separate(Math.floor(num / 60)) + ":" + String(num % 60);
}