function main( input ) {
    const a = input.split(' ')[0];
    const b = input.split(' ')[1];
    const c = parseInt( a+b, 10 );
    const cc = Math.floor(Math.sqrt( c ));
    console.log( ( Math.pow(cc, 2) === c ) ? 'Yes' : 'No' );
}

main( require('fs').readFileSync('/dev/stdin', 'utf8') )