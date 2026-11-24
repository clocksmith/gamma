function Main(input) {
  var s = input.split('');
  var result = 0;
  for (var i = 0; i < s.length; i++) {
    result = result + +s[i];
  }
  
  if(input % result === 0) {
    console.log('Yes');
  } else {
    console.log('No');
  }
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));