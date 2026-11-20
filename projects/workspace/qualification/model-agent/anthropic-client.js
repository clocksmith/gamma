// Fawn workspace model-driven comparison — minimal Anthropic Messages API client.
//
// Sends the frozen agent settings only: model, system prompt, tools, max output tokens and
// thinking disabled. No temperature, top_p or top_k is sent. Every billed attempt is charged
// to the spend ledger; transient provider errors are retried with backoff a bounded number of times.

const API_URL = 'https://api.anthropic.com/v1/messages';
const COUNT_URL = 'https://api.anthropic.com/v1/messages/count_tokens';
const API_VERSION = '2023-06-01';
const RETRYABLE = Object.freeze([429, 500, 502, 503, 529]);
const MAX_RETRIES = 3;
const BACKOFF_MS = 2000;

class ProviderError extends Error {
  constructor(status, body) {
    super(`provider ${status}: ${body.slice(0, 500)}`);
    this.status = status;
  }
}

function createClient({ apiKey, agent, ledger, fetchImpl = fetch, backoffMs = BACKOFF_MS }) {
  if (!apiKey) throw new Error('model API credentials are required');
  const headers = { 'x-api-key': apiKey, 'anthropic-version': API_VERSION, 'content-type': 'application/json' };
  async function post(url, body) {
    for (let attempt = 0; ; attempt += 1) {
      const response = await fetchImpl(url, { method: 'POST', headers, body: JSON.stringify(body) });
      const text = await response.text();
      if (response.ok) return JSON.parse(text);
      if (!RETRYABLE.includes(response.status) || attempt >= MAX_RETRIES) throw new ProviderError(response.status, text.replaceAll(apiKey, '[redacted]'));
      await new Promise((resolve) => setTimeout(resolve, backoffMs * 2 ** attempt));
    }
  }
  return {
    /** One model turn; the ledger refuses it if its worst case could cross the ceiling. */
    async turn({ system, tools, messages, purpose }) {
      const body = { model: agent.model, max_tokens: agent.maxOutputTokensPerTurn, system, tools, messages, thinking: agent.thinking };
      ledger.reserve(Buffer.byteLength(JSON.stringify(body)), agent.maxOutputTokensPerTurn, purpose);
      const response = await post(API_URL, body);
      ledger.charge(response.usage, purpose);
      return response;
    },
    /** Token count of one observation as the model receives it; counting is not billed. */
    async countTokens(text) {
      const response = await post(COUNT_URL, { model: agent.model, messages: [{ role: 'user', content: text }] });
      return response.input_tokens;
    },
  };
}

export { ProviderError, createClient };
