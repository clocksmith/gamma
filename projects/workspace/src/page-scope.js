// Page identity and observation permission are separate from workspace ownership.
import { REJECTION_CODES, workspaceError } from './errors.js';

export const MAIN_PAGE = 'main';
export function pageView(workspace, pageId = MAIN_PAGE) {
  if (!workspace.pages.has(pageId) || workspace.pages.get(pageId).closed) {
    throw workspaceError(REJECTION_CODES.INVALID_COMMAND, `Page ${pageId} is closed or unknown`);
  }
  const observations = new Map([...workspace.observations].filter(([, value]) => (value.pageId ?? MAIN_PAGE) === pageId));
  const observation = workspace.pageObservations.get(pageId) ?? null;
  return { ...workspace, observation, observations, observationVersion: observation?.observationVersion ?? 0 };
}

export function readGrant(workspace, command, url, now) {
  if (!workspace.scopedReads) return null;
  const origin = new URL(url).origin;
  const grant = [...workspace.grants.values()].find(value => value.ownerId === command.ownerId
    && (value.expiresAt === null || Date.parse(value.expiresAt) > now)
    && value.pageIds?.includes(command.pageId ?? MAIN_PAGE)
    && value.readRegions !== undefined && (url === 'about:blank' || value.targetOrigins.includes(origin)));
  if (!grant) throw workspaceError(REJECTION_CODES.UNAUTHORIZED_TARGET, 'This page has no current observation grant');
  return grant;
}

export function scopedRead(workspace, command, url, read, config, now) {
  const grant = readGrant(workspace, command, url, now);
  if (!grant || grant.readRegions === null) return read;
  if (read.regionGroups.length || read.regions.some(selector => !grant.readRegions.includes(selector))) {
    throw workspaceError(REJECTION_CODES.UNAUTHORIZED_TARGET, 'Read exceeds the selected page regions');
  }
  return { ...read, regions: grant.readRegions, readRoots: grant.readRegions };
}
