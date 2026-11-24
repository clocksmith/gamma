function main(input) {
  const str = input.split("\n").join("");
  const arr = countChar(str);
  for (let i = "a".charCodeAt(0); i <= "z".charCodeAt(); i++) {
    console.log(`${String.fromCharCode(i)} : ${arr[i] || 0}`);
  }
}

main(require("fs").readFileSync("/dev/stdin", "utf8"));

function countChar(str) {
  const arr = [];
  str
    .toLowerCase()
    .split("")
    .forEach(c => {
      arr[c.charCodeAt(0)]
        ? (arr[c.charCodeAt(0)] += 1)
        : (arr[c.charCodeAt(0)] = 1);
    });
  return arr;
}

