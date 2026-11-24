const MOD = 10**9+7
// factors[f].e+n-1、において max(n)=10**5, max(factors[f].e)=log(M)=log(10**9)=21
const N = 10**5+29

let fac = [...new Array(N)].fill(0)
let ifac = [...new Array(N)].fill(0)
const mul = (a,b) => ((a>>16)*b%MOD*65536+(a&65535)*b)%MOD;

const factorization = (n) => {
    let primes= []
    for(let i=2; i*i<=n; i++) {
        let exponent = 0
        while(n%i===0) {
            n /= i
            exponent++
        }
        if(exponent) {
            primes.push({p:i, e:exponent})
        }
    }
    
    if(n!==1) {
        primes.push({p:n, e:1})
    }
    return primes
}

const mpow = (x, n) => {
    ans = 1;
    let _x = x
    while(n != 0){
        if(n & 1) ans = mul(ans,_x);
        _x = mul(_x,_x);
        n = n >> 1;
    }
    return ans;
}

const comb = (n, r) => {
    if(n == 0 && r == 0) return 1;
    if(n < r || n < 0) return 0;
    const tmp = mul(ifac[n-r],ifac[r])
    return mul(tmp,fac[n])
}

const init = () => {
    fac[0] = 1;
    ifac[0] = 1;
    for(let i=0; i<N; i++){
        fac[i+1] = mul(fac[i],(i+1));
        ifac[i+1] = mpow(fac[i+1], MOD - 2)
    }
}

const main = (arg) => {
    let [n, m] = arg.split(" ").map(Number)
    let factors = factorization(m)
    let ans = 1
    init()
    Object.keys(factors).forEach(f=>{
        let a = factors[f].e+n-1
        let b = factors[f].e
        ans = mul(ans,comb(a, b))
    })
    console.log(ans)
}

main(require("fs").readFileSync("/dev/stdin", "utf8"));