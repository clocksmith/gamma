import { mkdir, rename, rm, writeFile } from "node:fs/promises";
import { randomUUID } from "node:crypto";
import { relative, resolve } from "node:path";
import { cancellationError } from "./cancellation.js";

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
    directory = "evidence/studies/simulation",
    canPublish = () => true
  }
) {
  if (!report || report.evidenceLabel !== "simulation") {
    throw new TypeError("Only simulation evidence can enter the simulation archive.");
  }
  if (!canPublish()) throw cancellationError();
  const archiveDirectory = resolve(projectRoot, directory);
  await mkdir(archiveDirectory, { recursive: true });
  const stem = [
    timestamp(report.generatedAt),
    slug(report.reportType, "simulation"),
    identitySlug(report),
    slug(report.seed, "seed"),
    scale(report),
    slug(jobId, "local"),
    randomUUID()
  ].join("-");
  const destination = resolve(archiveDirectory, `${stem}.json`);
  const temporary = resolve(archiveDirectory, `.${stem}.tmp`);
  try {
    await writeFile(temporary, `${JSON.stringify(report, null, 2)}\n`, {
      encoding: "utf8",
      flag: "wx"
    });
    if (!canPublish()) throw cancellationError();
    await rename(temporary, destination);
    if (!canPublish()) {
      await rm(destination, { force: true });
      throw cancellationError();
    }
  } finally {
    await rm(temporary, { force: true });
  }
  return {
    fileName: `${stem}.json`,
    relativePath: relative(projectRoot, destination)
  };
}
