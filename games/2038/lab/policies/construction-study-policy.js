// Diagnostic plans for the current candidate, not new rules or default personas.
// Only the public observation and the current legal decision are inspected.
const distance = (a, b) => (Math.abs(a.q - b.q) + Math.abs(a.r - b.r) +
  Math.abs(a.q + a.r - b.q - b.r)) / 2;

export function constructionStudyScore(packet, decision, treatment) {
  if (!["infrastructure_plan_v1", "research_deploy_plan_v1"].includes(treatment)) return null;
  const { self, board, round, publicTable } = packet.observation;
  const own = publicTable.players.find(player => player.seat === packet.seat);
  const facilities = own.facilities;
  const tile = id => board.find(candidate => candidate.tileId === id);
  const energy = board.filter(candidate => candidate.category === "energy" &&
    candidate.components.filter(component => component.type === "generator").length < 3);
  const infrastructure = treatment === "infrastructure_plan_v1";
  const hasCluster = own.megaClusters.length > 0;
  const fusionAvailable = round === 4 && !publicTable.players.some(player =>
    player.generators.some(generator => generator.sourceId === "fusion_demonstrator"));
  // Budget the next construction before selecting Build. Legal resolution still
  // owns actual prices, occupancy, host eligibility, and simultaneous contention.
  let goal = null;
  let runwayNeeded = 0;
  let computeNeeded = 0;
  if (!facilities.length) { goal = "first"; runwayNeeded = 2; }
  else if (infrastructure && round >= 2 && facilities.length < 2) {
    goal = "hosts"; runwayNeeded = own.generators.length ? 2 : 4;
  } else if (infrastructure && round >= 2 && !own.generators.length) {
    goal = "generator"; runwayNeeded = 2;
  } else if (infrastructure && round >= 2 && !hasCluster) {
    goal = "mega_cluster"; runwayNeeded = 3; computeNeeded = 2;
  } else if (infrastructure && fusionAvailable) {
    goal = "fusion_demonstrator"; runwayNeeded = 5;
  }
  const p = decision.parameters || {};
  if (decision.consequences?.stage === "action_selection") {
    if (!decision.consequences.resolvableWithoutTrade) return 0.001;
    const needsMoney = goal && self.runway < runwayNeeded;
    const ready = goal && !needsMoney && self.compute >= computeNeeded;
    return ({
      fund: needsMoney ? 200 : self.runway < 3 ? 25 : 1,
      build: ready ? 160 : 0.001,
      research: self.capability < 9 ? 60 : 8,
      deploy: self.canDeploy ? 70 : 0.001,
      influence: self.trust < 4 ? 30 : 12,
      organize: 0.1
    })[decision.actionId] ?? null;
  }
  if (decision.actionId === "build" && p.buildMode === "construction") {
    const destination = tile(p.destinationId);
    const project = p.project?.id;
    const adjacentFirst = facilities[0] && distance(destination, tile(facilities[0].tileId)) === 1;
    if (goal === "first" && p.facility && !project) {
      const futureHost = energy.some(source => distance(source, destination) === 1 &&
        source.facilitySpacesOpen > 0);
      const computeSite = ["cloud", "chip", "research"].includes(destination.category);
      return (computeSite ? 30 : 1) * (!infrastructure || futureHost ? 50 : 0.01);
    }
    if (goal === "hosts" && p.facility && adjacentFirst) {
      if (project === "generator") return p.project.sourceId === "clean_infrastructure" ? 2000 : 1000;
      if (!project && own.generators.some(generator => distance(tile(generator.tileId), destination) <= 1)) return 1000;
    }
    if (goal === "generator" && project === "generator" && !p.facility) {
      return facilities.every(facility => distance(tile(facility.tileId), destination) <= 1) ? 1000 : 0.001;
    }
    if (project === goal) return p.facility ? 1 : 2000;
    return 0.001;
  }
  // Both deliberate plans use the same immediate action choices and retain the
  // ordinary persona's trade, Headline, Research stopping and Influence policy.
  if (decision.actionId === "fund" && p.destinationId) {
    return (p.destinationCategory === "capital" ? 30 : 1) *
      (p.mode === "venture" && self.runway < Math.max(runwayNeeded, 3) ? 10 : 1);
  }
  if (decision.actionId === "research" && p.destinationId) {
    return p.destinationCategory === "research" ? 100 : p.destinationCategory === "cloud" ? 30 : 1;
  }
  if (decision.actionId === "deploy" && p.destinationId) return p.computeCost === 0 ? 100 : 1;
  return null;
}
