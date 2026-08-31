export function contentSourceFiles(graph, {
  graphPath = "content/graph.json",
  provenancePath = "content/provenance/numbers.json"
} = {}) {
  return [
    graphPath,
    graph.variables,
    graph.playerCopyContract,
    provenancePath,
    ...graph.artifacts.flatMap((artifact) => [
      artifact.source,
      artifact.ledger,
      ...(artifact.overlays || [])
    ])
  ].filter((path, index, paths) => path && paths.indexOf(path) === index);
}
