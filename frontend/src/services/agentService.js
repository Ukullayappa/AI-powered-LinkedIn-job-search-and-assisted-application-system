import {
  apiRequest,
} from "./apiClient";


export async function checkBackendHealth() {
  return apiRequest(
    "/api/health"
  );
}


export async function startAgent(
  agentSettings
) {
  return apiRequest(
    "/api/agent/start",
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify(
        agentSettings
      ),
    }
  );
}


export async function getAgentStatus() {
  return apiRequest(
    "/api/agent/status"
  );
}


export async function stopAgent() {
  return apiRequest(
    "/api/agent/stop",
    {
      method: "POST",
    }
  );
}