var input = '';
var readable = process.stdin;
readable.resume();
readable.setEncoding( 'utf-8' );
readable.on( 'data', function( chunk ) {
  input += chunk;
});

readable.on( 'end', function() {
  var data = input.split( '\n' );
  var output = [];
  var pattern = new Array( 152 ).join( "#." );
  for( var index=0; index<data.length; index++ ) {
    var nums = data[index].split( ' ' ).map( Number );
    if( 0 == nums[0] && 0 == nums[1] ) { break; }
    
    var row = [];
    for( var i=0; i<nums[0]; i++ ) {
      row.push( pattern.substr( i&1, nums[1]) );
    }
    output.push( row.join( '\n' )+'\n' );
  }
  console.log( output.join( '\n' )  );
});