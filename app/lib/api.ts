import { API_BASE_URL } from "./config";
import type {
  BackendSummary,
  ClusterResult,
  Corridor,
  NetworkInputs,
  OptimizationResult,
  RetailProfile,
} from "./types";

export async function fetchInitialDashboardData() {
  const [corridorResponse, retailResponse, healthResponse, clusterResponse] = await Promise.all([
    fetch(`${API_BASE_URL}/api/corridors`),
    fetch(`${API_BASE_URL}/api/retail-profiles`),
    fetch(`${API_BASE_URL}/api/health`),
    fetch(`${API_BASE_URL}/api/clusters`),
  ]);

  if (!corridorResponse.ok || !retailResponse.ok || !healthResponse.ok || !clusterResponse.ok) {
    throw new Error("Backend did not return healthy responses");
  }

  const [corridors, retailProfiles, health, clusters] = (await Promise.all([
    corridorResponse.json(),
    retailResponse.json(),
    healthResponse.json(),
    clusterResponse.json(),
  ])) as [Corridor[], RetailProfile[], { dataset: BackendSummary }, ClusterResult];

  return { corridors, retailProfiles, summary: health.dataset, clusters };
}

export async function fetchBackendOptimization(inputs: NetworkInputs) {
  const response = await fetch(`${API_BASE_URL}/api/optimise`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      corridorId: inputs.corridorId,
      anchorEnabled: inputs.anchorEnabled,
      anchorMultiplier: inputs.anchorMultiplier,
      maxDetour: inputs.maxDetour,
      guardrail: inputs.guardrail,
      minDriverScore: inputs.minDriverScore,
      maxClearanceMinutes: inputs.maxClearanceMinutes,
      preferContracted: inputs.preferContracted,
    }),
  });

  if (!response.ok) {
    throw new Error("Backend optimiser did not return a successful response");
  }

  const payload = (await response.json()) as { result: OptimizationResult };
  return payload.result;
}
