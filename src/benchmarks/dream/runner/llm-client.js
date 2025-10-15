/**
 * LLM Client
 * Unified interface for calling different LLM providers
 */

export class LLMClient {
  constructor(providers) {
    this.providers = providers;
  }

  /**
   * Complete a prompt using the specified provider
   */
  async complete(provider, prompt) {
    if (provider.name.startsWith('openai')) {
      return await this.completeOpenAI(provider, prompt);
    } else if (provider.name.startsWith('anthropic')) {
      return await this.completeAnthropic(provider, prompt);
    } else if (provider.name.startsWith('google') || provider.name.startsWith('gemini')) {
      return await this.completeGemini(provider, prompt);
    } else if (provider.name.startsWith('ollama')) {
      return await this.completeOllama(provider, prompt);
    } else {
      throw new Error(`Unknown provider: ${provider.name}`);
    }
  }

  /**
   * Call OpenAI API
   */
  async completeOpenAI(provider, prompt) {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${provider.apiKey}`
      },
      body: JSON.stringify({
        model: provider.model,
        messages: [
          {
            role: 'system',
            content: 'You are an expert programmer. Provide concise, accurate code solutions.'
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: 0.2,
        max_tokens: 4000
      })
    });

    if (!response.ok) {
      throw new Error(`OpenAI API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return {
      content: data.choices[0].message.content,
      model: provider.model,
      usage: data.usage
    };
  }

  /**
   * Call Anthropic API
   */
  async completeAnthropic(provider, prompt) {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': provider.apiKey,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: provider.model,
        max_tokens: 4000,
        messages: [
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: 0.2
      })
    });

    if (!response.ok) {
      throw new Error(`Anthropic API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return {
      content: data.content[0].text,
      model: provider.model,
      usage: data.usage
    };
  }

  /**
   * Call Google Gemini API
   */
  async completeGemini(provider, prompt) {
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${provider.model}:generateContent?key=${provider.apiKey}`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        contents: [
          {
            parts: [
              {
                text: `You are an expert programmer. Provide concise, accurate code solutions.\n\n${prompt}`
              }
            ]
          }
        ],
        generationConfig: {
          temperature: 0.2,
          maxOutputTokens: 4000
        }
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Gemini API error: ${response.status} ${response.statusText} - ${errorText}`);
    }

    const data = await response.json();

    if (!data.candidates || data.candidates.length === 0) {
      throw new Error('Gemini API returned no candidates');
    }

    return {
      content: data.candidates[0].content.parts[0].text,
      model: provider.model,
      usage: data.usageMetadata || {}
    };
  }

  /**
   * Call Ollama local API
   */
  async completeOllama(provider, prompt) {
    const url = `${provider.baseUrl}/api/generate`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: provider.model,
        prompt: `You are an expert programmer. Provide concise, accurate code solutions.\n\n${prompt}`,
        stream: false,
        options: {
          temperature: 0.2,
          num_predict: 4000
        }
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Ollama API error: ${response.status} ${response.statusText} - ${errorText}`);
    }

    const data = await response.json();

    return {
      content: data.response,
      model: provider.model,
      usage: {
        prompt_tokens: data.prompt_eval_count || 0,
        completion_tokens: data.eval_count || 0,
        total_tokens: (data.prompt_eval_count || 0) + (data.eval_count || 0)
      }
    };
  }
}
