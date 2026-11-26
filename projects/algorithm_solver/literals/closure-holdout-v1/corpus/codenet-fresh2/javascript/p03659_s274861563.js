function main( input ){

  var as = input.split( /\n/ )[1]
                .split( /\s/ )
                .map( function( n ){
                  return parseInt( n )
                } )

  var r = 0
  for( var i=1; i<as.length; i++ )
    r += as[i]

  var position = 1
  var l = as[0]
  var m = Math.abs( r - as[0] )

  for( ; as.length-1>position; position++ ){
    l += as[position]
    r -= as[position]

    if( m > Math.abs( l - r ) )
      m = Math.abs( l - r )
  }

  console.log( m )

}

main(
  require( 'fs' )
    .readFileSync( '/dev/stdin', 'utf8' )
)
