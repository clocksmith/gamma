export function contentSourceFiles(graph, {
  graphPath = "content/graph.json",
  provenancePath = "content/provenance/numbers.json"
} = {}) {
  return [
    graphPath,
    graph.variables,
    graph.world,
    provenancePath,
    ...(graph.supportingSources || []),
    ...Object.values(graph.excerpts || {}),
    ...Object.values(graph.contexts || {}).map(descriptor =>
      typeof descriptor === "string" ? descriptor : descriptor.path),
    ...graph.artifacts.flatMap(artifact => [artifact.source, ...(artifact.inputs || [])])
  ].filter((path, index, paths) => path && paths.indexOf(path) === index);
}
