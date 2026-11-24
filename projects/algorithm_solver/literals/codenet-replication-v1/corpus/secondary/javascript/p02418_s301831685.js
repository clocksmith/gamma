//line = require('fs').readFileSync('tmp', 'ascii').split('\r\n'); // win
line = require('fs').readFileSync('/dev/stdin', 'ascii').split('\n'); // linux

s = line[0] + line[0];
p = line[1];
if (s.indexOf(p) !== -1) console.log('Yes');
else console.log('No');