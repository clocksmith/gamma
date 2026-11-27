import { readdir } from "node:fs/promises";
import { basename, resolve } from "node:path";

export function validateProvenanceGraph(graph) {
  const relativePath = path => typeof path === "string" && path.length > 0 &&
    !path.startsWith("/") && !path.split("/").includes("..");
  const targets = new Set(graph.artifacts.map(artifact => artifact.target));
  if (!relativePath(graph.provenanceTarget) || !graph.provenanceTarget.startsWith("dist/review/docs/") ||
      targets.has(graph.provenanceTarget)) throw new Error("Provenance needs its own generated review destination.");
  for (const artifact of graph.artifacts) {
    if (artifact.target.startsWith("dist/review/docs/") && artifact.audience !== "review") {
      throw new Error(`Review destination has a conflicting audience: ${artifact.target}`);
    }
    if (artifact.target.startsWith("dist/docs/") && artifact.audience !== "player") {
      throw new Error(`Player documents cannot contain review outputs: ${artifact.target}`);
    }
  }
  const kitTargets = new Set();
  for (const file of graph.physicalKit.files) {
    if (!relativePath(file.source) || !relativePath(file.target) || kitTargets.has(file.target) ||
        !["player", "observer"].includes(file.audience) ||
        (file.audience === "observer") !== file.target.startsWith("observer/")) {
      throw new Error(`Invalid physical-kit audience or destination: ${file.target}`);
    }
    kitTargets.add(file.target);
  }
}

export function referenceSources(graph, reference, dependencies = {}) {
  const [kind, name] = reference.split(".");
  const known = dependencies[`${kind}.${name}`];
  if (known) return known;
  if (kind === "lore") return [graph.world];
  if (kind === "excerpts") return [graph.excerpts[name]];
  if (kind === "content") {
    const descriptor = graph.contexts[name];
    return typeof descriptor === "string" ? [descriptor] : [descriptor.path, ...(descriptor.inputs || [])];
  }
  return [graph.variables];
}

export async function documentSources(graph, root) {
  const documents = [];
  for (const group of graph.documentRendering) {
    const sources = new Set(group.files);
    for (const directory of group.directories) {
      if (directory.startsWith("dist/")) {
        for (const path of [...graph.artifacts.map(a => a.target), graph.provenanceTarget]) {
          if (path.startsWith(`${directory}/`) && path.endsWith(".md")) sources.add(path);
        }
      } else {
        for (const file of await readdir(resolve(root, directory))) {
          if (file.endsWith(".md")) sources.add(`${directory}/${file}`);
        }
      }
    }
    for (const source of sources) {
      const target = `${group.target}/${basename(source, ".md")}.html`;
      documents.push({source, target, audience:group.audience});
    }
  }
  return documents;
}

// Content provenance, not a complete build dependency graph. Directories and
// audiences come from the same declarations used by rendering and packaging.
export async function provenanceMarkdown(graph, artifacts, root) {
  const rows = artifacts.map(artifact => ({
    inputs: artifact.inputs, target: artifact.target, audience: artifact.audience
  }));
  const documents = await documentSources(graph, root);
  rows.push(...documents.map(({source, ...document}) => ({inputs:[source], ...document})));
  for (const gallery of Object.values(graph.galleryRendering.outputs)) {
    rows.push({inputs:Object.values(graph.galleryRendering.inputs), ...gallery});
  }
  for (const file of graph.physicalKit.files) {
    rows.push({inputs:[file.source], target:`dist/physical-kit/<kit-id>/${file.target}`, audience:file.audience});
  }
  for (const profile of Object.values(graph.deploymentProfiles)) {
    const audience = profile.deployable ? "player" : "review";
    for (const document of documents) {
      if (!profile.documents.includes("*") &&
          (document.audience !== "player" || !profile.documents.includes(basename(document.target)))) continue;
      const relative = document.target.replace(/^dist\/site\//, "");
      rows.push({inputs:[document.target], target:`${profile.outputRoot}/${relative}`, audience});
    }
    for (const id of profile.galleries) {
      const source = graph.galleryRendering.outputs[id].target;
      rows.push({inputs:[source], target:`${profile.outputRoot}/${basename(source)}`, audience});
    }
    for (const id of profile.interfaces) {
      const item = graph.interfaceArtifacts[id];
      rows.push({inputs:[item.source], target:`${profile.outputRoot}/${item.target}`, audience});
    }
    const runtime = profile.runtimeArtifacts.includes("*")
      ? artifacts.filter(a => a.target.startsWith("dist/runtime/")).map(a => a.target)
      : profile.runtimeArtifacts;
    for (const source of runtime) rows.push({inputs:[source], target:`${profile.outputRoot}/${source}`, audience});
  }
  const lines = rows.sort((a, b) => a.target.localeCompare(b.target)).map(row =>
    `| ${[...new Set(row.inputs)].sort().map(path => `\`${path}\``).join(" + ")} | \`${row.target}\` | ${row.audience} |`
  );
  return `# Mandate 2038 content provenance

Generated from content/graph.json and references resolved during compilation.
Edit the sources and graph, then run npm run content:build; do not edit this map.

This is content provenance, not a complete dependency graph or a claim of proper
layering. Rendering code, styles, image dependencies, and execution dependencies
are outside this map. Shared variables appear when content resolves them.
Kit IDs are assigned when a release is frozen; observer receipts and release
hashes are enumerated by that kit's manifest. Audiences are labels, not nodes.

| Content inputs | Destination | Audience |
| --- | --- | --- |
${lines.join("\n")}
`;
}
