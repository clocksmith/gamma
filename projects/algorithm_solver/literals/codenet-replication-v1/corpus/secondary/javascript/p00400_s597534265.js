var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var a=input.trim()-0;
if(a>=65 && a<=90)console.log(1);
else if(a>=97 && a<=122)console.log(2);
else console.log(0);
