//config = {stdin: 'tmp', newline: '\r\n'}; // win
config = {stdin: '/dev/stdin', newline: '\n'}; // linux

line = require('fs').readFileSync(config.stdin, 'ascii')
       .split(config.newline, 2);

number = line[0].split(' ');

dice = { 'T': number[0], 'S': number[1], 'E': number[2],
         'W': number[3], 'N': number[4], 'B': number[5] };

function turn_east(dst, src) {
  dst.T = src.W; dst.S = src.S; dst.E = src.T;
  dst.W = src.B; dst.N = src.N; dst.B = src.E;
}
function turn_north(dst, src) {
  dst.T = src.S; dst.S = src.B; dst.E = src.E;
  dst.W = src.W; dst.N = src.T; dst.B = src.N;
}
function turn_south(dst, src) {
  dst.T = src.N; dst.S = src.T; dst.E = src.E;
  dst.W = src.W; dst.N = src.B; dst.B = src.S;
}
function turn_west(dst, src) {
  dst.T = src.E; dst.S = src.S; dst.E = src.B;
  dst.W = src.T; dst.N = src.N; dst.B = src.W;
}

inst = line[1];
src = {};
for (i in dice) src[i] = dice[i];
turn = {'E': turn_east, 'N': turn_north, 'S': turn_south, 'W': turn_west}
for (i in inst) {
  tmp = src;
  src = dice;
  dice = tmp;
  turn[inst[i]](dice, src);
}

console.log(dice.T);