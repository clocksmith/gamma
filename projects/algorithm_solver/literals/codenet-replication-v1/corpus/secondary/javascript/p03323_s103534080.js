function Main(input) {
  var line = input.trim().split(' ');
  var A = Number(line[0]);
  var B = Number(line[1]);
  if (A <= 8 && B <= 8) {
    console.log('Yay!');
  } else {
    console.log(':(');
  }
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));
