const input = require('fs').readFileSync('/dev/stdin', 'utf8');

const data = input.split(' ');

function lastStr(str) {
   const length = str.length;
  return str.substring(length-1);
}

if(
  lastStr(data[0]) === data[1].substring(0,1) &&
  lastStr(data[1]) === data[2].substring(0,1) ){
  console.log('YES');
}else {
  console.log('NO');
}