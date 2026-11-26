"use strict";

function _toArray(arr) { return _arrayWithHoles(arr) || _iterableToArray(arr) || _nonIterableRest(); }

function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance"); }

function _iterableToArray(iter) { if (Symbol.iterator in Object(iter) || Object.prototype.toString.call(iter) === "[object Arguments]") return Array.from(iter); }

function _arrayWithHoles(arr) { if (Array.isArray(arr)) return arr; }

!function () {
  var P = 1e9 + 7;

  function* rangeRev(start, end) {
    for (var i = start - 1; i >= end; i--) {
      yield i;
    }
  }

  function makeArr(size, defaultValue) {
    if (!Array.isArray(size)) size = [size];
    if (1 === size.length) return new Array(size[0]).fill(defaultValue);

    var _size = size,
        _size2 = _toArray(_size),
        here = _size2[0],
        rest = _size2.slice(1);

    return new Array(here).fill(null).map(function () {
      return makeArr(rest, defaultValue);
    });
  }

  !function (input) {
    var L = input.split("\n")[0];
    var len = L.length;
    var dp = makeArr([2, len], 0);
    dp[0].push(1);
    dp[1].push(1);
    var _iteratorNormalCompletion = true;
    var _didIteratorError = false;
    var _iteratorError = undefined;

    try {
      for (var _iterator = rangeRev(len, 0)[Symbol.iterator](), _step; !(_iteratorNormalCompletion = (_step = _iterator.next()).done); _iteratorNormalCompletion = true) {
        var i = _step.value;
        if (0 == +("1" === L[i])) dp[0][i] = dp[0][i + 1];else {
          var nrm = 2 * dp[0][i + 1] % P;
          dp[0][i] = (nrm + dp[1][i + 1]) % P;
        }
        dp[1][i] = 3 * dp[1][i + 1] % P;
      }
    } catch (err) {
      _didIteratorError = true;
      _iteratorError = err;
    } finally {
      try {
        if (!_iteratorNormalCompletion && _iterator.return != null) {
          _iterator.return();
        }
      } finally {
        if (_didIteratorError) {
          throw _iteratorError;
        }
      }
    }

    console.log(dp[0][0]);
  }(require("fs").readFileSync("/dev/stdin", "utf8"));
}();
