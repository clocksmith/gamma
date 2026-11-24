var reader = require('readline').createInterface({
  input: process.stdin,
  output: process.stdout
});

var lines = [];
reader.on('line',(line) => {
          lines.push(line);
});

reader.on('close', () => {
          var line = lines[0];
  var elems = line.split(' ');
  var A = elems[1];
  var B = elems[2];
  var D = B - A;
  if ( D % 2 == 1){
    console.log('Borys');
  } else {
    console.log('Alice');
  }
});