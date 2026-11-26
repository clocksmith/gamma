/**
 * @param input string[][]
 */
function Main(input) {
  const line0 = input[0].split(' ').map(Number);
  const H = line0[0];
  const W = line0[1];
  const ss = input.slice(1);

  const checked = [];

  function getMax(y, x) {
    const stepMap = createStepMap(y, x);

    var max = 0, step;
    for (var i = 0; i < checked.length; i++) {
      step = stepMap[checked[i][0]][checked[i][1]];
      if (step > max) {
        max = step;
      }
    }

    return max;
  }

  function createStepMap(y, x) {
    const stepMap = ss.map((ssi) => ssi.split(''));

    fillRoute(y, x, stepMap);

    return stepMap;
  }

  function fillRoute(y, x, stepMap) {
    const ps = [[y, x, 0]];
    var p, py, px, pstep, current;

    while (p = ps.shift()) {
      py = p[0];
      px = p[1];
      current = stepMap[py][px];

      if (current !== '.') continue;

      pstep = p[2];
      stepMap[py][px] = pstep;

      // 左マス
      if (py > 0) {
        ps.push([py - 1, px, pstep + 1])
      }
      // 右マス
      if (py < H - 1) {
        ps.push([py + 1, px, pstep + 1])
      }
      // 上マス
      if (px > 0) {
        ps.push([py, px - 1, pstep + 1])
      }
      // 下マス
      if (px < W - 1) {
        ps.push([py, px + 1, pstep + 1])
      }
    }
  }

  var answer = 0;

  var y, x, max;
  for (y = 0; y < H; y++) {
    for (x = 0; x < W; x++) {
      if (ss[y][x] === '#') continue;

      if (checked.length > 0) {
        max = getMax(y, x);

        if (max > answer) {
          answer = max;
        }
      }

      checked.push([y, x]);
    }
  }

  console.log(answer);
}

Main(require("fs").readFileSync("/dev/stdin", "utf8").trim()
  .split('\n')
  // .map((v) => v.split(' '))
);
