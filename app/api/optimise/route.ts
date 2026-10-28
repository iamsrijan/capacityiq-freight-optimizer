import { findSiteCorridor, siteDataset } from "@/app/lib/site-dataset";
import { optimizeCorridor } from "@/app/lib/optimizer";
import type { NetworkInputs } from "@/app/lib/types";

const defaultInputs: NetworkInputs = {
  corridorId: "northeast",
  anchorEnabled: true,
  anchorMultiplier: 1,
  maxDetour: 120,
  guardrail: 74,
  minDriverScore: 72,
  maxClearanceMinutes: 480,
  preferContracted: true,
  airPricePriority: 60,
};

export async function POST(request: Request) {
  let payload: Partial<NetworkInputs>;

  try {
    payload = (await request.json()) as Partial<NetworkInputs>;
  } catch {
    return Response.json({ error: "Request body must be valid JSON" }, { status: 400 });
  }

  const inputs = { ...defaultInputs, ...payload };
  const corridor = findSiteCorridor(inputs.corridorId);

  if (!corridor) {
    return Response.json({ error: `Unknown corridor: ${inputs.corridorId}` }, { status: 404 });
  }

  const result = optimizeCorridor(
    corridor,
    inputs.anchorEnabled,
    inputs.anchorMultiplier,
    inputs.maxDetour,
    inputs.guardrail,
    inputs.minDriverScore,
    inputs.maxClearanceMinutes,
    inputs.preferContracted,
    siteDataset.airCarriers,
    inputs.airPricePriority,
  );

  return Response.json({
    corridor,
    result,
    dataset: siteDataset.summary,
  });
}
