//config = {input: 'tmp', newline: '\r\n'}; // win
config = {input: '/dev/stdin', newline: '\n'}; //linux

line = require('fs').readFileSync(config.input, 'ascii').trim();

geo = [0];
j = 0;
for (i in line) {
  if (line[i] === '\\') geo.push(--j);
  else if (line[i] === '/') geo.push(++j);
  else geo.push(j);
}

lv = []; // level of water surface
j = 0;
for (i in geo) {
  j = Math.max(j, geo[i]);
  lv.push(j);
}
j = geo[geo.length - 1];
for (i = geo.length - 1; i >= 0; i--) {
  j = Math.max(j, geo[i]);
  if (lv[i] > j) lv[i] = j;
}

segment = [];
prev = false;
for (i = 0; i < lv.length; i++) {
  cur = (lv[i] > geo[i]);
  if (!prev && cur) min = i;
  if (prev && !cur) segment.push([min, i - 1]);
  prev = cur;
}

res = segment.map(function (segment) {
  var max = segment[1];
  var sum = 0;
  for (var j = segment[0] - 1; j <= max; j++)
    sum += (lv[j] - (geo[j] + geo[j+1]) / 2);
  return sum;
});

console.log(res.reduce(function(p, c) { return p + c; }, 0));
if (res.length !== 0) console.log('%d %s', res.length, res.join(' '));
else console.log(0);