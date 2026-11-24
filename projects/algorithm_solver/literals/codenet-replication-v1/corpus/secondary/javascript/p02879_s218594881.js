'use strict'

const main = input => {
	const args = input.split('\n').map(arg => arg.split(' '))
	const A = parseInt(args[0][0], 10)
	const B = parseInt(args[0][1], 10)

	if (A < 10 && B < 10) console.log(A * B)
	else console.log(-1)
}

main(require('fs').readFileSync('/dev/stdin', 'utf8'))
