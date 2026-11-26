const input = require("fs").readFileSync("/dev/stdin", "utf8").split("/");
const c = input[0].replace("2017", "2018");
console.log(c + "/" + input[1] + "/" + input[2]);