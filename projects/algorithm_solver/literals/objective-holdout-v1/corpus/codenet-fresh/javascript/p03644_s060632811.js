'use strict'

const main = input => {
	const n = parseInt(input.trim(), 10)
	let maxNum = 0
	let maxCnt = -1

	for (let i = 1; i <= n; i++) {
		let tmpNum = i  
		let tmpCnt = 0

		while (true) {
			if (tmpNum % 2 === 1) break
			tmpNum /= 2
			tmpCnt++
		}

		if (tmpCnt > maxCnt) {
			maxNum = i
			maxCnt = tmpCnt
		}
	}

	console.log(maxNum)
}

main(require('fs').readFileSync('/dev/stdin', 'utf8'))
