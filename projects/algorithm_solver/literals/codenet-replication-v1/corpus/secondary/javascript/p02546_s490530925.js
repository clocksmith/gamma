function Main(input) {
  // 入力解析
  input = input.split("\n").map((v) => v.split(" "));
  // 使うのこれだけだから input に代入
  input = input[0][0];
  // 結果
  console.log(input.slice(-1) === "s" ? `${input}es` : `${input}s`);
}
// 魔法の呪文
Main(require("fs").readFileSync("/dev/stdin", "utf8"));