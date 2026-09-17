import type { Mode, NetworkInputs } from "./types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

export const initialNetworkInputs: NetworkInputs = {
  corridorId: "northeast",
  anchorEnabled: true,
  anchorMultiplier: 1,
  maxDetour: 120,
  guardrail: 74,
};

export const modeTargetFill: Record<Mode, number> = {
  road: 0.93,
  air: 0.84,
  sea: 0.78,
  staging: 0.88,
};

export function sameNetworkInputs(first: NetworkInputs, second: NetworkInputs) {
  return (
    first.corridorId === second.corridorId &&
    first.anchorEnabled === second.anchorEnabled &&
    first.anchorMultiplier === second.anchorMultiplier &&
    first.maxDetour === second.maxDetour &&
    first.guardrail === second.guardrail
  );
}
