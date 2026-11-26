var input = '';
var readable = process.stdin;
readable.resume();
readable.setEncoding( 'utf-8' );
readable.on( 'data', function( chunk ) {
  input += chunk;
});

readable.on( 'end', function() {
  var data = input.split( '\n' );
  var n = parseInt( data[0] );
  var x = data[1].split( ' ' ).map( Number );
  var y = data[2].split( ' ' ).map( Number );
  var Dxy = 0;
  var Dxy2 = 0;
  var Dxy3 = 0;
  var Dmax = 0;
  var t;
  for( var i=0; i<n; i++ ) {
    t = Math.abs( x[i]-y[i] );
    Dxy += t;
    Dxy2 += Math.pow( t, 2 );
    Dxy3 += Math.pow( t, 3 );
    Dmax = Math.max( Dmax, t );
  }
  console.log( Dxy );  
  console.log( Math.sqrt( Dxy2 ) );
  console.log( Math.pow( Dxy3, 1/3 ) );
  console.log( Dmax );
});