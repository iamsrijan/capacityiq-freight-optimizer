import { modeTargetFill } from "./config";
import type {
  Corridor,
  Mode,
  OptimizationResult,
  RecommendedAction,
  ScoredShipment,
  Shipment,
} from "./types";

const cargoFamilyFit: Record<string, number> = {
  "food-grade dry": 1,
  "chilled food": 0.88,
  "fresh produce": 0.82,
  "textile dry": 0.84,
  "container export": 0.78,
  "parcel returns": 0.74,
  electronics: 0.72,
  "fragile craft": 0.7,
  "secured samples": 0.66,
  "regulated pharma": 0.62,
  "regulated devices": 0.62,
};

const contractFit: Record<string, number> = {
  "dedicated fleet": 1,
  "fixed monthly": 0.94,
  "SLA contract": 0.92,
  "per-tonne contract": 0.84,
  "per-trip contract": 0.78,
  "spot market": 0.68,
};

function clampPercent(value: number) {
  return Math.max(0, Math.min(1, value));
}

function clearanceMinutes(shipment: Shipment) {
  return (
    (shipment.handlingMinutes ?? 0) +
    (shipment.securityMinutes ?? 0) +
    (shipment.customsMinutes ?? 0) +
    (shipment.layoverMinutes ?? 0)
  );
}

function shipmentCargoFit(shipment: Shipment) {
  return cargoFamilyFit[shipment.cargoFamily ?? ""] ?? 0.76;
}

function shipmentContractFit(shipment: Shipment) {
  return contractFit[shipment.contractType ?? "spot market"] ?? 0.68;
}

function shipmentScheduleFit(shipment: Shipment, maxClearanceMinutes: number) {
  if (shipment.mode !== "air" && shipment.compatibility !== "regulated") {
    return 1;
  }

  const clearance = clearanceMinutes(shipment);
  const softTarget = maxClearanceMinutes * 0.5;
  const overage = Math.max(0, clearance - softTarget);
  return clampPercent(1 - overage / Math.max(maxClearanceMinutes, 1));
}

function riskFlagsFor(
  shipment: Shipment,
  minDriverScore: number,
  maxClearanceMinutes: number,
  preferContracted: boolean,
) {
  const flags: string[] = [];
  const driverScore = shipment.driverScore ?? 78;
  const routeTrips = shipment.routeFamiliarityTrips ?? 0;
  const familyFit = shipmentCargoFit(shipment);

  if (driverScore < minDriverScore) {
    flags.push("Driver score below scenario floor");
  }
  if (routeTrips < 8) {
    flags.push("Low route familiarity");
  }
  if (familyFit < 0.68) {
    flags.push("Strict cargo segregation needed");
  }
  if (shipment.mode === "air" && clearanceMinutes(shipment) > maxClearanceMinutes) {
    flags.push("Airport clearance exceeds scenario cap");
  }
  if (preferContracted && shipment.contractType === "spot market") {
    flags.push("Spot-market capacity");
  }

  return flags;
}

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
  const vehicle = shipment.vehicleProfile?.toLowerCase() ?? "compatible vehicle";
  const driverScore = shipment.driverScore ?? 78;
  const routeTrips = shipment.routeFamiliarityTrips ?? 0;

  if (shipment.mode === "air") {
    return `Book ${shipment.matchedTonnes} t of ${cargo} into ${vehicle} with a ${driverScore} driver score and keep road movement limited to first and last mile transfers.`;
  }

  if (shipment.mode === "sea") {
    return `Batch ${shipment.matchedTonnes} t of ${cargo} through ${vehicle} and use the corridor only for drayage and consolidation.`;
  }

  if (shipment.mode === "staging") {
    return `Stage ${shipment.matchedTonnes} t of ${cargo} in ${vehicle}, then release it with the next compatible dispatch wave.`;
  }

  return `Assign ${shipment.matchedTonnes} t of ${cargo} to ${vehicle} on ${corridor.returnLane} with a detour cap of ${maxDetour} km and ${routeTrips} prior route trips.`;
}

function schedulePlanFor(shipment: ScoredShipment, maxClearanceMinutes: number) {
  const clearance = clearanceMinutes(shipment);
  const peakWindow = shipment.peakWindow ?? "next dispatch wave";

  if (shipment.mode === "air") {
    return `${shipment.airportPair ?? "nearest cargo gateway"}; peak window ${peakWindow}; ${clearance} min handling/security/customs against ${maxClearanceMinutes} min cap.`;
  }

  return `Dispatch in ${peakWindow}; historical transit ${shipment.avgTransitHours ?? 0} h; ${clearance} min handling buffer.`;
}

function buildRecommendedActions(
  corridor: Corridor,
  accepted: ScoredShipment[],
  availableByMode: Map<Mode, number>,
  maxDetour: number,
  guardrail: number,
  maxClearanceMinutes: number,
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
        `Score ${shipment.score} from route fit, reliability, revenue, cargo fit and operating quality`,
        `${shipment.detourKm} km detour is within the ${maxDetour} km policy`,
        `${shipment.compatibility} cargo clears the ${guardrail}% compatibility guardrail`,
        `${shipment.contractType ?? "spot market"} with driver score ${shipment.driverScore ?? 78} and ${shipment.routeFamiliarityTrips ?? 0} prior route trips`,
        `${shipment.window} service window with ${shipment.reliability}% reliability`,
      ],
      revenue,
      emptyKmAvoided,
      capacityShare: Math.round((shipment.matchedTonnes / available) * 100),
      timing: `Pickup ${shipment.pickupWindow ?? shipment.window}; deliver by ${
        shipment.deliveryWindow ?? shipment.window
      }`,
      assignedVehicle: shipment.vehicleProfile,
      driverScore: shipment.driverScore ?? 78,
      routeFamiliarityTrips: shipment.routeFamiliarityTrips ?? 0,
      contractType: shipment.contractType,
      averageTransitHours: shipment.avgTransitHours,
      averageMonthlyCost: shipment.avgMonthlyCost,
      compatibilityNote: shipment.compatibilityNote,
      schedulePlan: schedulePlanFor(shipment, maxClearanceMinutes),
      riskFlags: shipment.riskFlags ?? [],
    };
  });
}

function scoreShipment(
  shipment: Shipment,
  maxDetour: number,
  guardrail: number,
  minDriverScore: number,
  maxClearanceMinutes: number,
  preferContracted: boolean,
) {
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
  const cargoFit = shipmentCargoFit(shipment);
  const driverFit = (shipment.driverScore ?? 78) / 100;
  const routeFamiliarityFit = Math.min((shipment.routeFamiliarityTrips ?? 0) / 50, 1);
  const contractStrength = shipmentContractFit(shipment);
  const timingFit = shipmentScheduleFit(shipment, maxClearanceMinutes);
  const guardrailPenalty = ((guardrail - 50) / 50) * (1 - compatibilityFit) * 22;
  const driverPenalty = Math.max(0, minDriverScore - (shipment.driverScore ?? 78)) * 0.35;
  const contractPenalty = preferContracted && shipment.contractType === "spot market" ? 5 : 0;
  const clearancePenalty = (Math.max(0, clearanceMinutes(shipment) - maxClearanceMinutes) / 60) * 4;

  const score = Math.round(
    routeFit * 22 +
      reliabilityFit * 17 +
      compatibilityFit * 13 +
      cargoFit * 12 +
      revenueFit * 10 +
      urgencyFit * 6 +
      driverFit * 8 +
      routeFamiliarityFit * 6 +
      contractStrength * 4 +
      timingFit * 2 -
      guardrailPenalty -
      driverPenalty -
      contractPenalty -
      clearancePenalty,
  );

  return {
    score: Math.max(0, Math.min(100, score)),
    scoring: {
      routeFit: Number(routeFit.toFixed(2)),
      reliabilityFit: Number(reliabilityFit.toFixed(2)),
      compatibilityFit: Number(compatibilityFit.toFixed(2)),
      cargoFit: Number(cargoFit.toFixed(2)),
      driverFit: Number(driverFit.toFixed(2)),
      routeFamiliarityFit: Number(routeFamiliarityFit.toFixed(2)),
      contractFit: Number(contractStrength.toFixed(2)),
      scheduleFit: Number(timingFit.toFixed(2)),
    },
    riskFlags: riskFlagsFor(shipment, minDriverScore, maxClearanceMinutes, preferContracted),
  };
}

function buildOperationalSummary(
  accepted: ScoredShipment[],
  declined: ScoredShipment[],
  maxClearanceMinutes: number,
) {
  const acceptedCount = Math.max(accepted.length, 1);
  const contracted = accepted.filter((item) => item.contractType && item.contractType !== "spot market");
  const compatibilityCleared = accepted.filter(
    (item) => !(item.riskFlags ?? []).includes("Strict cargo segregation needed"),
  );

  return {
    avgDriverScore: Math.round(
      accepted.reduce((sum, item) => sum + (item.driverScore ?? 78), 0) / acceptedCount,
    ),
    avgRouteFamiliarityTrips: Math.round(
      accepted.reduce((sum, item) => sum + (item.routeFamiliarityTrips ?? 0), 0) / acceptedCount,
    ),
    contractedShare: Math.round((contracted.length / acceptedCount) * 100),
    compatibilityCleared: Math.round((compatibilityCleared.length / acceptedCount) * 100),
    airClearanceBreaches: declined.filter(
      (item) => item.mode === "air" && clearanceMinutes(item) > maxClearanceMinutes,
    ).length,
    strictCompatibilityRejected: declined.filter((item) =>
      ["Cargo segregation risk too high", "Guardrail confidence too low"].includes(item.reason),
    ).length,
    avgMonthlyCost: Math.round(
      accepted.reduce((sum, item) => sum + (item.avgMonthlyCost ?? 0), 0) / acceptedCount,
    ),
  };
}

export function optimizeCorridor(
  corridor: Corridor,
  anchorEnabled: boolean,
  anchorMultiplier: number,
  maxDetour: number,
  guardrail: number,
  minDriverScore = 72,
  maxClearanceMinutes = 360,
  preferContracted = true,
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
    .map((shipment) => {
      const scoring = scoreShipment(
        shipment,
        maxDetour,
        guardrail,
        minDriverScore,
        maxClearanceMinutes,
        preferContracted,
      );

      return {
        ...shipment,
        score: scoring.score,
        scoring: scoring.scoring,
        riskFlags: scoring.riskFlags,
        matchedTonnes: 0,
        reason: "",
      };
    })
    .sort((a, b) => b.score - a.score);

  const accepted: ScoredShipment[] = [];
  const declined: ScoredShipment[] = [];
  const threshold = Math.max(55, guardrail - 12);

  scored.forEach((shipment) => {
    const modeRemaining = remainingBookable.get(shipment.mode) ?? 0;
    const incompatible =
      guardrail >= 82 &&
      (shipment.compatibility === "chilled" || shipment.compatibility === "regulated");
    const cargoBlocked = guardrail >= 82 && shipmentCargoFit(shipment) < 0.68;
    const detourBlocked = shipment.mode !== "air" && shipment.detourKm > maxDetour;
    const driverBlocked = (shipment.driverScore ?? 78) < minDriverScore;
    const clearanceBlocked = shipment.mode === "air" && clearanceMinutes(shipment) > maxClearanceMinutes;

    if (modeRemaining <= 0) {
      declined.push({ ...shipment, reason: "No capacity left in this mode" });
      return;
    }

    if (detourBlocked) {
      declined.push({ ...shipment, reason: "Detour exceeds lane policy" });
      return;
    }

    if (driverBlocked) {
      declined.push({ ...shipment, reason: "Driver score below scenario floor" });
      return;
    }

    if (clearanceBlocked) {
      declined.push({ ...shipment, reason: "Airport clearance window too tight" });
      return;
    }

    if (cargoBlocked) {
      declined.push({ ...shipment, reason: "Cargo segregation risk too high" });
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
      maxClearanceMinutes,
    ),
    operationalSummary: buildOperationalSummary(accepted, declined, maxClearanceMinutes),
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
