process.stdin.resume();
process.stdin.setEncoding('utf8');

var lines = [];
var reader = require('readline').createInterface({
  input: process.stdin,
  output: process.stdout
});
reader.on('line', (line) => {
  lines.push(line);
});
reader.on('close', () => {
    const a = lines[0].split("");
    let flg = (a.indexOf("N") >= 0 &&  a.lastIndexOf("S") < 0) ||
        (a.indexOf("W") >= 0 && a.indexOf("E") < 0 ) ||
        (a.indexOf("W") < 0 && a.indexOf("E") >= 0 ) ||
        (a.indexOf("N") < 0 &&  a.lastIndexOf("S") >= 0)
    console.log(!flg?"Yes":"No");
});
