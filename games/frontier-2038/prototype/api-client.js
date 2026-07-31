const localHosts = new Set(["localhost", "127.0.0.1"]);
const bridgeStorageKey = "m3t4-local-bridge-token";

export const bridgeRequired = !localHosts.has(window.location.hostname);
export const localBridgeBase = "http://127.0.0.1:8038";

let bridgeToken = bridgeRequired
  ? sessionStorage.getItem(bridgeStorageKey) || ""
  : "";

export function getBridgeToken() {
  return bridgeToken;
}

export function setBridgeToken(value) {
  bridgeToken = String(value || "").trim();
  if (!bridgeRequired) return;
  if (bridgeToken) sessionStorage.setItem(bridgeStorageKey, bridgeToken);
  else sessionStorage.removeItem(bridgeStorageKey);
}

function apiUrl(path) {
  return bridgeRequired ? `${localBridgeBase}${path}` : path;
}

export async function apiFetch(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const request = {
    ...options,
    headers
  };
  if (bridgeRequired) {
    if (!bridgeToken) {
      throw new Error("Connect the local bridge before starting server work.");
    }
    headers.set("X-M3T4-Bridge-Token", bridgeToken);
    request.targetAddressSpace = "local";
  }
  try {
    return await fetch(apiUrl(path), request);
  } catch (error) {
    // Monitoring cancellation is an intentional local UI action, not a bridge failure.
    if (error?.name === "AbortError") throw error;
    if (!bridgeRequired) throw error;
    throw new Error(
      "The local bridge could not be reached. Start npm run dev, allow Chrome local-network access, and confirm the pairing token.",
      { cause: error }
    );
  }
}

export async function connectBridge(token) {
  setBridgeToken(token);
  try {
    const response = await apiFetch("/api/bridge");
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Bridge pairing failed.");
    return result;
  } catch (error) {
    setBridgeToken("");
    throw error;
  }
}
