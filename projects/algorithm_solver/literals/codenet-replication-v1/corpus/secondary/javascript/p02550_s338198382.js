const main = (arg) => {
    const [N,X,M] = arg.split(" ").map(Number)
    
    let tmp = [...new Array(M)].fill(0)
    let mods = [...new Array(M)].fill(0)
    tmp[0] = X
    mods[0] = X
    // console.log(tmp)
    let i=1, loopStart=0
    for(; i<M; i++) {
        tmp[i] = tmp[i-1]**2 % M
        if(mods[tmp[i]]!==0) {
            // loop detected
            loopStart = mods[tmp[i]]
            break
        } else {
            mods[tmp[i]] = i
        }
    }
    const loopEnd = i
    const loopNum = loopEnd-loopStart
    const loopCount = loopNum===0 ? 0 : Math.floor((N-loopStart)/(loopNum))
    // console.log(`i=${i}, loopStart=${loopStart}, loopEnd=${loopEnd}, loopCount=${loopCount}`)

    let ans = 0
    let sumOfLoop = 0
    for(i=loopStart; i<loopEnd; i++) {
        sumOfLoop += tmp[i]
    }
    ans += sumOfLoop*loopCount
    
    // console.log(`sumOfLoop=${sumOfLoop}`)

    // add first something before loop starts
    for(i=0; i<loopStart; i++) {
        ans += tmp[i]
    }

    // add last something after loop ends
    const restCount = loopNum===0 ? 0 : N-loopStart-(loopNum)*loopCount
    // console.log(`restCount=${restCount}`)
    
    let rest = 0
    for(i=loopStart; i<loopStart+restCount; i++) {
        rest += tmp[i]
    }
    // console.log(`rest=${rest}`)
    ans += rest
    console.log(ans)
}

main(require("fs").readFileSync("/dev/stdin", "utf8"));