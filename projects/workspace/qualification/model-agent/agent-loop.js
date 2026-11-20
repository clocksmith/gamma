// Fawn workspace model-driven comparison — one model-driven task.
//
// The frozen system prompt, task prompt and tools go to the model unchanged on both sides. The
// conversation is checkpointed before each tool runs, so a restarted agent resumes it; a tool
// call whose result was lost gets the same restart notice on both sides. The turn limit and the
// per-task input budget end a task as a failure.

const RESTART_NOTICE = 'The agent process restarted; the result of this call was not recorded.';

class AgentKilled extends Error {
  constructor() {
    super('agent process ended');
    this.code = 'agent-killed';
  }
}

/**
 * @returns {Promise<{status: string, artifact?: string, reason?: string, summary?: string}>}
 */
async function runModelTask({ client, frozen, agent, backend, checkpoint, alive, observations, purpose }) {
  const live = () => {
    if (!alive()) throw new AgentKilled();
  };
  const state = checkpoint.get();
  const messages = state.messages ?? [{ role: 'user', content: frozen.taskPrompt }];
  const last = messages.at(-1);
  if (last?.role === 'assistant') {
    const lost = last.content.filter((block) => block.type === 'tool_use');
    messages.push({
      role: 'user',
      content: lost.map((block) => ({ type: 'tool_result', tool_use_id: block.id, content: RESTART_NOTICE, is_error: true })),
    });
  }
  let { turns = 0, inputTokens = 0, outputTokens = 0 } = state;
  const save = () => checkpoint.update({ messages, turns, inputTokens, outputTokens });
  for (;;) {
    live();
    if (turns >= agent.maxTurnsPerTask) return { status: 'turn-limit' };
    if (inputTokens >= agent.maxInputTokensPerTask) return { status: 'budget-exceeded' };
    const response = await client.turn({ system: frozen.system, tools: frozen.tools, messages, purpose });
    live();
    turns += 1;
    inputTokens += response.usage.input_tokens;
    outputTokens += response.usage.output_tokens;
    messages.push({ role: 'assistant', content: response.content });
    save();
    const calls = response.content.filter((block) => block.type === 'tool_use');
    if (calls.length === 0) return { status: 'ended-without-finish' };
    const results = [];
    for (const call of calls) {
      if (call.name === 'finish') return { status: 'completed', artifact: call.input.artifact ?? null, summary: call.input.summary };
      if (call.name === 'request_human_review') return { status: 'human-review', reason: call.input.reason };
      let output;
      try {
        output = await backend.execute(call.name, call.input);
      } catch (error) {
        live();
        output = { text: `Error: ${error.message}`, isError: true };
      }
      live();
      if (call.name === 'observe') observations.push(output.text);
      results.push({ type: 'tool_result', tool_use_id: call.id, content: output.text, is_error: output.isError });
    }
    messages.push({ role: 'user', content: results });
    save();
  }
}

export { AgentKilled, RESTART_NOTICE, runModelTask };
