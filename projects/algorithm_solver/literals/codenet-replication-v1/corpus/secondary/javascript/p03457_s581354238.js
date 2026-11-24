const input = require("fs").readFileSync("/dev/stdin", "utf8")
;(input => {
  
    const lines = input.split('\n')
    const N = lines[0] - 0

    const T = []
    for (let i = 1; i <= N; i++) {
         T.push(lines[i].split(' ').map(Number))
    }
  
    const f = (a, b) => {
      const dist = Math.abs(a[1] + a[2] - b[1] - b[2])
      const t = b[0] - a[0]
      if (t < dist) {
        return false
      } else if ((t - dist) % 2) {
        return false
      }
      return true
    }
    
    let ans = 'Yes'
    let t = null
    let p = [0, 0, 0]
    for (let i = 0; i < N; i++) {
        const t = T[i]
	    if (f(p, t)) {
            p = t
        } else {
            ans = 'No'
            break
        }
    }

    console.log(ans)
  
})(input)
