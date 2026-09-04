export function contentSourceFiles(graph, {
  graphPath = "content/graph.json",
  provenancePath = "content/provenance/numbers.json"
} = {}) {
  return [
    graphPath,
    graph.variables,
    graph.world,
    provenancePath,
    ...Object.values(graph.contexts || {}).map(descriptor =>
      typeof descriptor === "string" ? descriptor : descriptor.path),
    ...graph.artifacts.map(artifact => artifact.source)
  ].filter((path, index, paths) => path && paths.indexOf(path) === index);
}
