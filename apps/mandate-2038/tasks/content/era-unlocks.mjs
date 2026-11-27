// Project names and unlock Eras come from their mechanical definitions.
// Keep references intact so the compiler records the source dependency.
export function deriveEraUnlocks(game, projects) {
  return {
    ...game,
    rounds: game.rounds.map(round => ({
      ...round,
      newThisEra: [
        ...round.newThisEra,
        ...projects.filter(project => project.unlockedRound === round.number)
          .map(project => `\${content.projects.byId.${project.id}.name}`)
      ]
    }))
  };
}
