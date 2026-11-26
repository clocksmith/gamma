'use strict'
let n, m, visited, graph

const trace = arr => {
  let tmp = ''
  for (let i in arr) {
    for (let j in arr[i]) {
      tmp += arr[i][j] ? '@' : '-'
    }
    tmp += '\n'
  }
  console.log(tmp)
}

const dfs = i => {
  visited[i] = true
  for (let i2 = 0; i2 < n; i2++) {
    //訪問済みか、辺がなかったら探索スキップ
    if (visited[i2] || graph[i][i2] == false) continue //スキップ
    dfs(i2)
  }
}

function main(input) {
  // data
  input = input.split('\n').map(v => v.split(' ').map(v => ~~v))
  n = input[0][0]
  m = input[0][1]
  const edges = input.slice(1, -1)

  //連結グラフは隣接行列表現＝二次元配列
  graph = Array.apply(null, {
    length: n
  }).map(
    v =>
      (v = Array.apply(null, {
        length: n
      }).fill(false))
  )

  for (let i = 0; i < m; i++) {
    let a = edges[i][0] - 1
    let b = edges[i][1] - 1
    graph[a][b] = true
    graph[b][a] = true
  }
  visited = Array.apply(null, {
    length: n
  }).fill(false)

  let cnt = 0
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      if (graph[i][j]) {
        //辺を見つけたら

        //辺を取り除く
        graph[i][j] = false
        graph[j][i] = false

        //探索
        visited.fill(false) //初期化

        dfs(0) //全て訪問できるかチェック
        if (!visited.every(v=>v==true)) cnt++

        //元に戻す
        graph[i][j] = true
        graph[j][i] = true
      }
    }
  }

  //   count(graph)
  console.log(cnt / 2)
  // trace(graph)
}
main(require("fs").readFileSync("/dev/stdin", "utf8"))