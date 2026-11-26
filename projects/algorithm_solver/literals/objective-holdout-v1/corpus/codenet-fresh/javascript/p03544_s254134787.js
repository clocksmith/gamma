"use strict"

function main(input) {
  //一部の正解がjsで扱う最大値を越えるため、文字列として扱う。
  //計算は配列を使った筆算（上の配列と下の配列を計算、桁上がりも対応）にて行う

  input = Number(input)

  let numbers = ["2", "1"]

  for (let i = 2; i <= input; i++) {
    const cal = (a, b) => {

      //左詰の配列だと計算しづらいのでreverse
      let aa = a
        .split("")
        .map(v => ~~v)
        .reverse()
      let bb = b
        .split("")
        .map(v => ~~v)
        .reverse()

      let cc = []
      let digit = 0
      //各配列の値についてaa[i] + bb[i]する=筆算 桁数の大きい方の回数
      for (let i = 0; i < bb.length; i++) {
        let tmp = Number(aa[i])
          ? Number(aa[i]) + Number(bb[i]) + digit
          : Number(bb[i]) + digit //
        digit = 0

        if (tmp >= 10) {
          digit = Math.floor(tmp / 10)
          tmp = tmp % 10
        } else {
          digit = 0
        }
        cc.push(tmp)

      }
      if (digit > 0) cc.push(digit)

      return cc.reverse().join("") //array -> recerse -> string
    }
    let tmp = cal(numbers[i - 2], numbers[i - 1])
    numbers.push(tmp)
  }
  console.log(numbers.pop()) //string

}
main(require("fs").readFileSync("/dev/stdin", "utf8"))