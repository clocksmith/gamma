import { connectedFacilityIds } from './local-power-connections.js';

const distance = (a, b) => Math.max(Math.abs(a.q - b.q), Math.abs(a.r - b.r), Math.abs(a.q + a.r - b.q - b.r));

// These nominal amounts also drive actual Facility Production. Reading them
// neither applies caps nor earns resources, awards, or faction triggers.
export function facilityComputeCapacity(board, facility) {
  const tile = board.find(t => t.instanceId === facility.tileId);
  const base = facility.category === 'cloud' ? 2
    : ['research', 'chip'].includes(facility.category) ? 1
    : facility.category === 'energy' && tile?.id === 'grid_reactor' ? 1 : 0;
  return base + (facility.customSilicon ? 1 : 0);
}

export function facilityContractResource(board, facility) {
  const tile = board.find(t => t.instanceId === facility.tileId);
  if (!tile) return null;
  if (['research', 'cloud', 'chip'].includes(tile.category) || tile.id === 'grid_reactor') return 'compute';
  if (['consumer', 'capital', 'talent', 'media', 'government'].includes(tile.category) || tile.id === 'renewable_basin') return 'runway';
  return null;
}

// Fixed hosts, their owners, adjacency and present connections are authoritative.
// Cached powered flags and creation dates are deliberately irrelevant.
export function activeJointVenture(state, contract) {
  if (contract.kind !== 'joint_venture' || contract.left.seat === contract.right.seat) return false;
  const hosts = [contract.left, contract.right].map(end => {
    const owner = state.players.find(p => p.seat === end.seat);
    const host = owner?.facilities.find(f => f.id === end.facilityId);
    const tile = host && state.board.find(t => t.instanceId === host.tileId);
    return owner && host && tile && connectedFacilityIds(state.board, owner).has(host.id) ? tile : null;
  });
  return Boolean(hosts[0] && hosts[1] && distance(...hosts) === 1);
}

export function nominalComputeCapacity(state, player) {
  const connected = connectedFacilityIds(state.board, player);
  let value = player.facilities.filter(f => connected.has(f.id)).reduce((sum, f) => sum + facilityComputeCapacity(state.board, f), 0);
  for (const project of player.projects || []) {
    if (project.projectId !== 'mega_cluster' || !connected.has(project.hostId)) continue;
    const production = state.projectDocument.projects.find(p => p.id === project.projectId)?.production;
    if (production?.resource === 'compute') value += production.amount;
  }
  for (const contract of state.contracts || []) {
    if (!activeJointVenture(state, contract)) continue;
    const other = contract.left.seat === player.seat ? contract.right : contract.right.seat === player.seat ? contract.left : null;
    if (!other) continue;
    const host = state.players.find(p => p.seat === other.seat).facilities.find(f => f.id === other.facilityId);
    if (facilityContractResource(state.board, host) === 'compute') value += 1;
  }
  return value;
}

function controlledCategoryCount(state, player) {
  const categories = new Set();
  for (const tile of state.board) {
    if (tile.category === 'frontier') continue;
    const scores = state.players.map(p => ({seat:p.seat, value:[...p.pieces, ...p.facilities].filter(piece => piece.tileId === tile.instanceId).length}));
    const maximum = Math.max(...scores.map(s => s.value));
    const leaders = scores.filter(s => s.value === maximum);
    if (maximum > 0 && leaders.length === 1 && leaders[0].seat === player.seat) categories.add(tile.category);
  }
  return categories.size;
}

const resourceMetrics = new Set(['customers', 'capability', 'runway', 'trust', 'scrutiny']);
const metricNames = new Set([...resourceMetrics, 'facilities', 'connected_facilities', 'connected_infrastructure', 'active_ventures', 'controlled_categories', 'compute_capacity']);
function metricValue(metric, state, player) {
  if (resourceMetrics.has(metric)) return player[metric];
  if (metric === 'facilities') return player.facilities.length;
  if (metric === 'active_ventures') return (state.contracts || []).filter(c => (c.left?.seat === player.seat || c.right?.seat === player.seat) && activeJointVenture(state, c)).length;
  if (metric === 'controlled_categories') return controlledCategoryCount(state, player);
  if (metric === 'compute_capacity') return nominalComputeCapacity(state, player);
  const connected = connectedFacilityIds(state.board, player);
  if (metric === 'connected_facilities') return connected.size;
  if (metric === 'connected_infrastructure') return connected.size + (player.projects || []).filter(p => p.projectId === 'mega_cluster' && connected.has(p.hostId)).length;
  throw new Error(`Unknown Era Mandate metric: ${metric}`);
}

export function evaluateEraMandate(card, state, player) {
  if (!metricNames.has(card.metric) || !['max', 'min'].includes(card.direction) || !Array.isArray(card.qualification)) throw new Error('Invalid current-state Era Mandate definition');
  const value = metricValue(card.metric, state, player);
  const qualified = card.qualification.every(({metric, minimum}) => {
    if (!metricNames.has(metric) || !Number.isFinite(minimum)) throw new Error('Invalid Era Mandate qualification');
    return metricValue(metric, state, player) >= minimum;
  });
  return {qualified, value, direction:card.direction};
}
