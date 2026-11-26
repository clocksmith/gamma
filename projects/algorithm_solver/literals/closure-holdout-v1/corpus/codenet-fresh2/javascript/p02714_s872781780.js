(v=>{
    const n = ~~(v.split('\n')[0])
    const s = v.split('\n')[1]
    let tmp = {'r':0, 'g':0, 'b':0}
    const arr = {'r':[],'g':[],'b':[]}
    for(let i=0;i<n;++i){
        if(s[i]=='R')tmp.r++
        if(s[i]=='G')tmp.g++
        if(s[i]=='B')tmp.b++
        arr.r.push(tmp.r)
        arr.g.push(tmp.g)
        arr.b.push(tmp.b)
    }
    const sm = {'r':arr.r[n-1], 'g':arr.g[n-1], 'b':arr.b[n-1]}
    const keys = {'R': 'gb', 'G':'br', 'B': 'rg'}
    let res = 0
    for(let i=1; i<n-1; ++i){
        const k = keys[s[i]]
    
        res += arr[k[0]][i-1] * (sm[k[1]] - arr[k[1]][i])
        res += arr[k[1]][i-1] * (sm[k[0]] - arr[k[0]][i])
        for(j=i-1,jj=i+1;j>=0&&jj<n;j--,jj++){
            if(s[i]!=s[j] && s[j]!=s[jj] && s[jj] != s[i]){
                res--
            }
        }
    }
    console.log(res)
})(require("fs").readFileSync("/dev/stdin", "utf8"))