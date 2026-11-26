//Main(`31415926535897932384626433832795028841971693993751058209749445923078164062862089986280`);

function Main(input) {
  const data = input.trim().split("").map(Number);
  const sum = data.reduce((acc,crt) => acc+crt);

  console.log(sum%9 === 0? 'Yes':'No');
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));