import type { LucideIcon } from "lucide-react";

export type Mode = "road" | "air" | "sea" | "staging";
export type CorridorId = string;
export type RetailId = string;

export type ModeCapacity = {
  mode: Mode;
  label: string;
  capacity: number;
  available: number;
  status: string;
};

export type Shipment = {
  id: string;
  shipper: string;
  cargo: string;
  origin: string;
  destination: string;
  tonnes: number;
  mode: Mode;
  revenuePerTon: number;
  detourKm: number;
  reliability: number;
  compatibility: "ambient" | "dry" | "fragile" | "regulated" | "chilled";
  window: string;
  urgency: number;
  priority?: string;
  pickupWindow?: string;
  deliveryWindow?: string;
};

export type Corridor = {
  id: CorridorId;
  name: string;
  anchor: string;
  origin: string;
  destination: string;
  returnLane: string;
  recurring: string;
  distanceKm: number;
  baselineEmptyKm: number;
  baseAnchorTonnes: number;
  vehicles: number;
  serviceLevel: number;
  region?: string;
  modes: ModeCapacity[];
  shipments: Shipment[];
};

export type ScoredShipment = Shipment & {
  score: number;
  matchedTonnes: number;
  reason: string;
};

export type RetailProfile = {
  id: RetailId;
  name: string;
  terminal: string;
  passengerMix: string;
  weeklyFlights: number;
  baseRevenue: number;
  compliance: string;
  assortments: Array<{ label: string; share: number; uplift: number }>;
};

export type BackendSummary = {
  corridors: number;
  capacityRows: number;
  shipments: number;
  retailProfiles: number;
  retailAssortments: number;
  hubs: number;
  partners: number;
  totalCapacityTonnes: number;
};

export type DataSource = "loading" | "backend" | "fallback";
export type OptimizationSource = "loading" | "backend" | "browser-fallback";

export type ModeUtilizationResult = ModeCapacity & {
  availableTonnes: number;
  bookableTonnes?: number;
  remainingTonnes: number;
  reserveTonnes?: number;
  usedTonnes: number;
  utilisation: number;
};

export type OptimizationResult = {
  accepted: ScoredShipment[];
  declined: ScoredShipment[];
  remaining: Partial<Record<Mode, number>>;
  modeUtilisation?: ModeUtilizationResult[];
  adjustedCapacity: number;
  matchedTonnes: number;
  revenue: number;
  emptyKmAvoided: number;
  costSaved: number;
  loadFactor: number;
  unitCostDrop: number;
  anchorTonnes: number;
};

export type NetworkInputs = {
  corridorId: CorridorId;
  anchorEnabled: boolean;
  anchorMultiplier: number;
  maxDetour: number;
  guardrail: number;
};

export type MetricIcon = LucideIcon;
