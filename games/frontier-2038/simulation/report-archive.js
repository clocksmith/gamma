import { mkdir, rename, writeFile } from "node:fs/promises";
import { relative, resolve } from "node:path";

function slug(value, fallback = "report") {
  const normalized = String(value || fallback)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 64);
  return normalized || fallback;
}

function timestamp(value) {
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) {
    throw new TypeError("Report requires a valid generatedAt.");
  }
  return date.toISOString().replace(/[-:.]/g, "");
}

function scale(report) {
  if (report.reportType === "strategy_evolution") {
    return `g${report.generations}-p${report.population}-${report.runsPerSeat}x${report.playerCount}`;
  }
  if (report.reportType === "rule_search") {
    return `v${report.iterations}-${report.runsPerVariant}x${report.playerCount}`;
  }
  return `${report.runs}x${report.playerCount}`;
}

function identitySlug(report) {
  const version = slug(report.game?.version, "unversioned");
  const fingerprint = String(report.game?.rulesetFingerprint || "unknown")
    .replace(/^sha256:/, "")
    .slice(0, 12);
  return `${version}-${slug(fingerprint, "unknown")}`;
}

export async function archiveSimulationReport(
  report,
  {
    projectRoot,
    jobId,
    directory = "studies/simulation"
  }
) {
  if (!report || report.evidenceLabel !== "simulation") {
    throw new TypeError("Only simulation evidence can enter the simulation archive.");
  }
  const archiveDirectory = resolve(projectRoot, directory);
  await mkdir(archiveDirectory, { recursive: true });
  const stem = [
    timestamp(report.generatedAt),
    slug(report.reportType, "simulation"),
    identitySlug(report),
    slug(report.seed, "seed"),
    scale(report),
    slug(jobId, "local")
  ].join("-");
  const destination = resolve(archiveDirectory, `${stem}.json`);
  const temporary = resolve(archiveDirectory, `.${stem}.tmp`);
  await writeFile(temporary, `${JSON.stringify(report, null, 2)}\n`, {
    encoding: "utf8",
    flag: "wx"
  });
  await rename(temporary, destination);
  return {
    fileName: `${stem}.json`,
    relativePath: relative(projectRoot, destination)
  };
}
