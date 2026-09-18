import { modeTargetFill } from "./config";
import type {
  Corridor,
  Mode,
  OptimizationResult,
  RecommendedAction,
  ScoredShipment,
  Shipment,
} from "./types";

function routeAnchorNode(label: string) {
  return label.split("+")[0].split("/")[0].trim() || label;
}

function routeAnchorNodes(label: string) {
  const nodes: string[] = [];

  label
    .replace(/\+/g, "/")
    .split("/")
    .forEach((part) => {
      const node = part.trim();
      if (node && !nodes.includes(node)) {
        nodes.push(node);
      }
    });

  return nodes.length ? nodes : [label];
}

function routeNodesFor(corridor: Corridor, shipment: ScoredShipment) {
  const corridorOrigin = routeAnchorNode(corridor.origin);
  const corridorOriginNodes = routeAnchorNodes(corridor.origin);
  const corridorDestination = routeAnchorNode(corridor.destination);
  const corridorDestinationNodes = routeAnchorNodes(corridor.destination);

  if (shipment.mode === "air") {
    return [
      shipment.origin,
      `${corridorDestination} air cargo window`,
      `${corridorOrigin} air gateway`,
      shipment.destination,
    ].filter((node, index, nodes) => node && nodes.indexOf(node) === index);
  }

  if (shipment.mode === "sea") {
    return [
      shipment.origin,
      `${corridorDestination} feeder consolidation`,
      `${corridorOrigin} port linkage`,
      shipment.destination,
    ].filter((node, index, nodes) => node && nodes.indexOf(node) === index);
  }

  if (shipment.mode === "staging") {
    return [
      shipment.origin,
      `${corridorDestination} staging area`,
      `${corridorOrigin} consolidation hub`,
      shipment.destination,
    ].filter((node, index, nodes) => node && nodes.indexOf(node) === index);
  }

  return [
    shipment.origin,
    ...corridorDestinationNodes,
    ...[...corridorOriginNodes].reverse(),
    shipment.destination,
  ].filter((node, index, nodes) => node && nodes.indexOf(node) === index);
}

function instructionFor(corridor: Corridor, shipment: ScoredShipment, maxDetour: number) {
  const cargo = shipment.cargo.toLowerCase();

  if (shipment.mode === "air") {
    return `Book ${shipment.matchedTonnes} t of ${cargo} into the next belly-cargo window and keep road movement limited to first and last mile transfers.`;
  }

  if (shipment.mode === "sea") {
    return `Batch ${shipment.matchedTonnes} t of ${cargo} through the feeder or port linkage and use the corridor only for drayage and consolidation.`;
  }

  if (shipment.mode === "staging") {
    return `Stage ${shipment.matchedTonnes} t of ${cargo} at the consolidation buffer, then release it with the next compatible dispatch wave.`;
  }

  return `Assign ${shipment.matchedTonnes} t of ${cargo} to return truck capacity on ${corridor.returnLane} with a detour cap of ${maxDetour} km.`;
}

function buildRecommendedActions(
  corridor: Corridor,
  accepted: ScoredShipment[],
  availableByMode: Map<Mode, number>,
  maxDetour: number,
  guardrail: number,
): RecommendedAction[] {
  return accepted.slice(0, 6).map((shipment, index) => {
    const route = routeNodesFor(corridor, shipment);
    const revenue = shipment.matchedTonnes * shipment.revenuePerTon;
    const emptyKmAvoided = Math.round(
      (shipment.matchedTonnes / (shipment.mode === "road" ? 16 : 24)) *
        Math.max(120, corridor.distanceKm - shipment.detourKm),
    );
    const available = Math.max(availableByMode.get(shipment.mode) ?? 0, 1);

    return {
      id: `ACT-${String(index + 1).padStart(2, "0")}-${shipment.id}`,
      shipmentId: shipment.id,
      headline: `Move ${shipment.matchedTonnes} t of ${shipment.cargo} by ${shipment.mode}`,
      shipper: shipment.shipper,
      cargo: shipment.cargo,
      mode: shipment.mode,
      matchedTonnes: shipment.matchedTonnes,
      route,
      routeText: route.join(" -> "),
      operatingInstruction: instructionFor(corridor, shipment, maxDetour),
      why: [
        `Score ${shipment.score} from route fit, reliability, revenue and urgency`,
        `${shipment.detourKm} km detour is within the ${maxDetour} km policy`,
        `${shipment.compatibility} cargo clears the ${guardrail}% compatibility guardrail`,
        `${shipment.window} service window with ${shipment.reliability}% reliability`,
      ],
      revenue,
      emptyKmAvoided,
      capacityShare: Math.round((shipment.matchedTonnes / available) * 100),
      timing: `Pickup ${shipment.pickupWindow ?? shipment.window}; deliver by ${
        shipment.deliveryWindow ?? shipment.window
      }`,
    };
  });
}

function scoreShipment(shipment: Shipment, maxDetour: number, guardrail: number) {
  const routeFit = Math.max(0, 1 - shipment.detourKm / Math.max(maxDetour, 1));
  const reliabilityFit = shipment.reliability / 100;
  const revenueFit = Math.min(shipment.revenuePerTon / 12000, 1);
  const urgencyFit = shipment.urgency / 100;
  const compatibilityFit =
    shipment.compatibility === "dry" || shipment.compatibility === "ambient"
      ? 1
      : shipment.compatibility === "fragile"
        ? 0.86
        : shipment.compatibility === "regulated"
          ? 0.74
          : 0.42;
  const guardrailPenalty = ((guardrail - 50) / 50) * (1 - compatibilityFit) * 22;

  return Math.round(
    routeFit * 32 +
      reliabilityFit * 24 +
      compatibilityFit * 22 +
      revenueFit * 15 +
      urgencyFit * 7 -
      guardrailPenalty,
  );
}

export function optimizeCorridor(
  corridor: Corridor,
  anchorEnabled: boolean,
  anchorMultiplier: number,
  maxDetour: number,
  guardrail: number,
): OptimizationResult {
  const anchorFactor = anchorEnabled ? anchorMultiplier : 0.54;
  const availableByMode = new Map<Mode, number>();
  const remainingBookable = new Map<Mode, number>();

  corridor.modes.forEach((item) => {
    const availableCapacity = Math.round(item.capacity * (item.available / 100) * anchorFactor);
    // The fallback model mirrors the backend: keep operating reserve so bars do not unrealistically peg at 100%.
    const bookableCapacity = availableCapacity ? Math.round(availableCapacity * modeTargetFill[item.mode]) : 0;
    availableByMode.set(item.mode, availableCapacity);
    remainingBookable.set(item.mode, bookableCapacity);
  });

  const scored = corridor.shipments
    .map((shipment) => ({
      ...shipment,
      score: scoreShipment(shipment, maxDetour, guardrail),
      matchedTonnes: 0,
      reason: "",
    }))
    .sort((a, b) => b.score - a.score);

  const accepted: ScoredShipment[] = [];
  const declined: ScoredShipment[] = [];
  const threshold = Math.max(55, guardrail - 12);

  scored.forEach((shipment) => {
    const modeRemaining = remainingBookable.get(shipment.mode) ?? 0;
    const incompatible =
      guardrail >= 82 &&
      (shipment.compatibility === "chilled" || shipment.compatibility === "regulated");
    const detourBlocked = shipment.mode !== "air" && shipment.detourKm > maxDetour;

    if (modeRemaining <= 0) {
      declined.push({ ...shipment, reason: "No capacity left in this mode" });
      return;
    }

    if (detourBlocked) {
      declined.push({ ...shipment, reason: "Detour exceeds lane policy" });
      return;
    }

    if (shipment.score < threshold || incompatible) {
      declined.push({ ...shipment, reason: "Guardrail confidence too low" });
      return;
    }

    const matchedTonnes = Math.min(shipment.tonnes, modeRemaining);
    remainingBookable.set(shipment.mode, modeRemaining - matchedTonnes);
    accepted.push({
      ...shipment,
      matchedTonnes,
      reason: matchedTonnes === shipment.tonnes ? "Full match" : `${matchedTonnes} t partial match`,
    });
  });

  const adjustedCapacity = corridor.modes.reduce((sum, item) => {
    return sum + Math.round(item.capacity * (item.available / 100) * anchorFactor);
  }, 0);
  const matchedTonnes = accepted.reduce((sum, item) => sum + item.matchedTonnes, 0);
  const revenue = accepted.reduce((sum, item) => sum + item.matchedTonnes * item.revenuePerTon, 0);
  const emptyKmAvoided = Math.round(
    accepted.reduce((sum, item) => {
      const distance = Math.max(120, corridor.distanceKm - item.detourKm);
      const vehicleEquivalent = item.matchedTonnes / (item.mode === "road" ? 16 : 24);
      return sum + vehicleEquivalent * distance;
    }, 0),
  );
  const costSaved = emptyKmAvoided * 68;
  const loadFactor = adjustedCapacity ? Math.round((matchedTonnes / adjustedCapacity) * 100) : 0;
  const baselineLoadFactor = anchorEnabled ? 19 : 11;
  const unitCostDrop = Math.max(0, Math.min(34, Math.round((loadFactor - baselineLoadFactor) * 0.62)));
  const anchorTonnes = Math.round(corridor.baseAnchorTonnes * anchorFactor);
  const totalRemaining = new Map<Mode, number>();

  corridor.modes.forEach((item) => {
    const availableCapacity = availableByMode.get(item.mode) ?? 0;
    const bookableCapacity = availableCapacity ? Math.round(availableCapacity * modeTargetFill[item.mode]) : 0;
    const bookableRemaining = remainingBookable.get(item.mode) ?? 0;
    const usedCapacity = Math.max(0, bookableCapacity - bookableRemaining);
    totalRemaining.set(item.mode, Math.max(0, availableCapacity - usedCapacity));
  });

  return {
    accepted,
    declined,
    recommendedActions: buildRecommendedActions(
      corridor,
      accepted,
      availableByMode,
      maxDetour,
      guardrail,
    ),
    remaining: Object.fromEntries(totalRemaining) as Partial<Record<Mode, number>>,
    adjustedCapacity,
    matchedTonnes,
    revenue,
    emptyKmAvoided,
    costSaved,
    loadFactor,
    unitCostDrop,
    anchorTonnes,
  };
}
