var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var s = input.trim();
while (s.match(/\(\)/)) s = s.replace(/\(\)/g, "");
var arr = s.split("*");
if (arr.length < 2) console.log(0);
else console.log(Math.min(arr[0].replace(/[^\(]/g, "").length, arr[1].replace(/[^\)]/g, "").length));
