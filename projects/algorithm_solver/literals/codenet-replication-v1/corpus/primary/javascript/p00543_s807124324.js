var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr = input.trim().split("\n");
var nm = (arr.shift()).split(" ").map(Number);
arr = arr.map(Number);
for (var i = 1; i <= nm[1]; i++) {
   for (var j = 0; j < arr.length - 1; j++) {
      var a = arr[j] % i;
      var b = arr[j + 1] % i;
      if (b < a) {
         var memo = arr[j + 1];
         arr[j + 1] = arr[j];
         arr[j] = memo;
      }
   }
}
console.log(arr.join("\n"));