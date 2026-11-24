function token(s) {
  var len = s.length;
  return function (target, pos) {
    return target.substr(pos, len) === s ? [true, s, pos + len]
      : [false, null, pos];
  };
}

function choice() {
  var parsers = arguments;
  return function (target, pos) {
    for (var i = 0; i < parsers.length; i++) {
      var parsed = parsers[i](target, pos);
      if (parsed[0]) return parsed;
    }
    return [false, null, pos];
  };
}

function seq() {
  var parsers = arguments;
  return function (target, pos) {
    var result = [];
    var nextPos = pos;
    for (var i = 0; i < parsers.length; i++) {
      var parsed = parsers[i](target, nextPos);
      if (!parsed[0]) return [false, null, pos];
      result.push(parsed[1]);
      nextPos = parsed[2];
    }
    return [true, result, nextPos];
  };
}

function lazy(f) {
  var parser;
  return function (target, position) {
    if (!parser) parser = f();
    return parser(target, position);
  };
}

function fmap(parser, f) {
  return function (target, pos) {
    var result = parser(target, pos);
    return result[0] ? [result[0], f(result[1]), result[2]]
      : result;
  };
}

function oneOf(s) {
  var d = {};
  for (var i = 0; i < s.length; i++) d[s[i]] = s[i];
  return function (target, pos) {
    var c = target.substr(pos, 1);
    return d[c] ? [true, c, pos + 1] : [false, null, pos];
  };
}

(function (stdin) {
  var formulaP = lazy(function () {
    var andP = fmap(seq(token('('), formulaP, token('*'), formulaP, token(')')), function (x) {
      return { op: '*', fs: [x[1], x[3]] };
    });
    var orP = fmap(seq(token('('), formulaP, token('+'), formulaP, token(')')), function (x) {
      return { op: '+', fs: [x[1], x[3]] };
    });
    var impP = fmap(seq(token('('), formulaP, token('->'), formulaP, token(')')), function (x) {
      return { op: '->', fs: [x[1], x[3]] };
    });
    var notP = fmap(seq(token('-'), formulaP), function (x) {
      return { op: '-', fs: [x[1]] };
    });
    var valP = fmap(oneOf('abcdefghijkTF'), function (x) { return { val: x, fs: [] }; });
    return choice(andP, orP, impP, notP, valP);
  });
  var equationP = fmap(seq(formulaP, token('='), formulaP), function (x) {
    return { left: x[0], right: x[2] };
  });

  stdin.toString().split('\n').forEach(function (s) {
    if (s == '#') process.exit(0);
    var r = equationP(s, 0);
    var isValid = true;
    for (var i = 0; i < (1 << 11); i++) {
      var toBool = function (c) {
        if (c === 'T') return true;
        if (c === 'F') return false;
        return !!(i >> (c.charCodeAt() - 'a'.charCodeAt()) & 1);
      };
      var evalF = function (f) {
        switch (f.fs.length) {
          case 0: return toBool(f.val);
          case 1: return !evalF(f.fs[0]);
          case 2:
            switch (f.op) {
              case '*': return evalF(f.fs[0]) && evalF(f.fs[1]);
              case '+': return evalF(f.fs[0]) || evalF(f.fs[1]);
              case '->': return !evalF(f.fs[0]) || evalF(f.fs[1]);
            }
        }
      };
      isValid &= evalF(r[1].left) === evalF(r[1].right);
    }
    console.log(isValid ? 'YES' : 'NO');
  });
})(require('fs').readFileSync('/dev/stdin', 'utf8'));