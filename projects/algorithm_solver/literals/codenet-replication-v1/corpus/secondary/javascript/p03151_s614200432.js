function sum_arr(arr) {
    return arr.reduce(function(prev, current, i, arr) {
        return prev+current;
    });
};


function main(arg) {
	arg = arg.split("\n")
	var N = arg[0].split(" ")[0]
	var A = arg[1].split(" ").map(e => Number(e))
	var B = arg[2].split(" ").map(e => Number(e))

	// var sum_a = sum_arr(A)
	// var sum_b = sum_arr(B)
	// var diff = sum_a - sum_b
	// // console.log(diff)
	// if (sum_a < sum_b) {
	// 	console.log(-1)
	// 	return;
	// }
// console.log(diff)

	var diffs = []
	var diff_m = 0

	var counter = 0

	for (var i = 0; i < A.length; i++) {
		var tmp = A[i] - B[i]
		if (tmp < 0) {
			diff_m += tmp
			counter++
		} else {
			diffs.push(tmp)
		}
	}

	if (diff_m >= 0) {
		console.log(0)
		return
	}

	diffs.sort((a,b) => b - a)

	for (var i = 0; i < diffs.length; i++) {
		diff_m += diffs[i]
		counter++

		if (diff_m > 0) {
			break
		}
	}

	if (diff_m  <= 0) {
		console.log(-1)
		return;
	}

	console.log(counter)

}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));