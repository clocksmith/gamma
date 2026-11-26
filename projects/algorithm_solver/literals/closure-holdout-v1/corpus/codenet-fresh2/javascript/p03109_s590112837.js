function Main(input) {
	if (new Date('2019/04/30') >= new Date(input)) {
    console.log('Heisei');
  } else {
    console.log('TBD');
  }
}
//*この行以降は編集しないでください（標準入出力から一度に読み込み、Mainを呼び出します）
Main(require("fs").readFileSync("/dev/stdin", "utf8"));
