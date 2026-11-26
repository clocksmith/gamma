'use strict';
(function(stdin) {
  var lines  = stdin.toString().split('\n');
  var result = (function(data) {

    return data.replace(/([a-z])|([A-Z])/g,function(c,lower,upper) {
      if (lower) return c.toUpperCase();
      if (upper) return c.toLowerCase();
    });
  
  }(lines[0]
  ));
  console.log(result);
}(require('fs').readFileSync('/dev/stdin', 'utf8')));