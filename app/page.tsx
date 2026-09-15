"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ArrowRightLeft,
  Box,
  CheckCircle2,
  CircleDollarSign,
  Clock3,
  Database,
  Gauge,
  PackageCheck,
  Plane,
  RefreshCw,
  Route,
  ShieldCheck,
  Ship,
  ShoppingBag,
  SlidersHorizontal,
  TrendingUp,
  Truck,
  Warehouse,
  XCircle,
} from "lucide-react";

type Mode = "road" | "air" | "sea" | "staging";
type CorridorId = string;
type RetailId = string;

type ModeCapacity = {
  mode: Mode;
  label: string;
  capacity: number;
  available: number;
  status: string;
};

type Shipment = {
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
};

type Corridor = {
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
  modes: ModeCapacity[];
  shipments: Shipment[];
};

type ScoredShipment = Shipment & {
  score: number;
  matchedTonnes: number;
  reason: string;
};

type RetailProfile = {
  id: RetailId;
  name: string;
  terminal: string;
  passengerMix: string;
  weeklyFlights: number;
  baseRevenue: number;
  compliance: string;
  assortments: Array<{ label: string; share: number; uplift: number }>;
};

type BackendSummary = {
  corridors: number;
  capacityRows: number;
  shipments: number;
  retailProfiles: number;
  retailAssortments: number;
  hubs: number;
  partners: number;
  totalCapacityTonnes: number;
};

type DataSource = "loading" | "backend" | "fallback";
type OptimizationSource = "loading" | "backend" | "browser-fallback";

type ModeUtilizationResult = ModeCapacity & {
  availableTonnes: number;
  bookableTonnes?: number;
  remainingTonnes: number;
  reserveTonnes?: number;
  usedTonnes: number;
  utilisation: number;
};

type OptimizationResult = {
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

type NetworkInputs = {
  corridorId: CorridorId;
  anchorEnabled: boolean;
  anchorMultiplier: number;
  maxDetour: number;
  guardrail: number;
};

const initialNetworkInputs: NetworkInputs = {
  corridorId: "northeast",
  anchorEnabled: true,
  anchorMultiplier: 1,
  maxDetour: 120,
  guardrail: 74,
};

function sameNetworkInputs(first: NetworkInputs, second: NetworkInputs) {
  return (
    first.corridorId === second.corridorId &&
    first.anchorEnabled === second.anchorEnabled &&
    first.anchorMultiplier === second.anchorMultiplier &&
    first.maxDetour === second.maxDetour &&
    first.guardrail === second.guardrail
  );
}

const modeMeta = {
  road: { label: "Road", Icon: Truck, className: "mode-road" },
  air: { label: "Air", Icon: Plane, className: "mode-air" },
  sea: { label: "Sea", Icon: Ship, className: "mode-sea" },
  staging: { label: "Staging", Icon: Warehouse, className: "mode-staging" },
} satisfies Record<Mode, { label: string; Icon: typeof Truck; className: string }>;

const modeTargetFill: Record<Mode, number> = {
  road: 0.93,
  air: 0.84,
  sea: 0.78,
  staging: 0.88,
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

const corridors: Corridor[] = [
  {
    id: "northeast",
    name: "Northeast Backhaul",
    anchor: "Britannia Kolkata to Guwahati loop",
    origin: "Kolkata / Siliguri",
    destination: "Guwahati + Upper Assam",
    returnLane: "Northeast to East and North India",
    recurring: "6 dispatch waves per week",
    distanceKm: 1120,
    baselineEmptyKm: 87000,
    baseAnchorTonnes: 2420,
    vehicles: 176,
    serviceLevel: 91,
    modes: [
      {
        mode: "road",
        label: "Truck backhaul slots",
        capacity: 2680,
        available: 72,
        status: "High empty-return exposure",
      },
      {
        mode: "air",
        label: "Belly cargo windows",
        capacity: 94,
        available: 38,
        status: "Premium urgent cargo",
      },
      {
        mode: "sea",
        label: "Haldia feeder linkage",
        capacity: 360,
        available: 31,
        status: "Slow bulk overflow",
      },
      {
        mode: "staging",
        label: "Guwahati consolidation",
        capacity: 430,
        available: 64,
        status: "Cross-dock buffer",
      },
    ],
    shipments: [
      {
        id: "NE-01",
        shipper: "Assam Tea Consortium",
        cargo: "Packaged tea cartons",
        origin: "Dibrugarh",
        destination: "Kolkata",
        tonnes: 680,
        mode: "road",
        revenuePerTon: 4200,
        detourKm: 48,
        reliability: 94,
        compatibility: "dry",
        window: "48 h",
        urgency: 72,
      },
      {
        id: "NE-02",
        shipper: "Brahmaputra Craft Collective",
        cargo: "Bamboo panels and handicrafts",
        origin: "Jorhat",
        destination: "Delhi NCR",
        tonnes: 360,
        mode: "staging",
        revenuePerTon: 5200,
        detourKm: 82,
        reliability: 86,
        compatibility: "fragile",
        window: "72 h",
        urgency: 55,
      },
      {
        id: "NE-03",
        shipper: "Healthline Distributors",
        cargo: "Regulated pharma samples",
        origin: "Guwahati",
        destination: "Kolkata airport",
        tonnes: 42,
        mode: "air",
        revenuePerTon: 12800,
        detourKm: 14,
        reliability: 91,
        compatibility: "regulated",
        window: "18 h",
        urgency: 96,
      },
      {
        id: "NE-04",
        shipper: "Eastern Electronics",
        cargo: "Reverse logistics parcels",
        origin: "Shillong",
        destination: "Bengaluru",
        tonnes: 190,
        mode: "staging",
        revenuePerTon: 6100,
        detourKm: 105,
        reliability: 82,
        compatibility: "ambient",
        window: "96 h",
        urgency: 47,
      },
      {
        id: "NE-05",
        shipper: "Hill Produce Network",
        cargo: "Speciality ginger and citrus",
        origin: "Aizawl",
        destination: "Kolkata",
        tonnes: 210,
        mode: "road",
        revenuePerTon: 4600,
        detourKm: 166,
        reliability: 78,
        compatibility: "chilled",
        window: "36 h",
        urgency: 81,
      },
      {
        id: "NE-06",
        shipper: "PortLink Forwarders",
        cargo: "Containerised tea export overflow",
        origin: "Guwahati ICD",
        destination: "Haldia port",
        tonnes: 310,
        mode: "sea",
        revenuePerTon: 3400,
        detourKm: 58,
        reliability: 88,
        compatibility: "dry",
        window: "5 d",
        urgency: 36,
      },
    ],
  },
  {
    id: "west",
    name: "Western FMCG Loop",
    anchor: "Britannia Pune to Rajasthan distribution",
    origin: "Pune / Nashik",
    destination: "Jaipur + Jodhpur",
    returnLane: "Rajasthan to Maharashtra and South",
    recurring: "4 dispatch waves per week",
    distanceKm: 940,
    baselineEmptyKm: 52000,
    baseAnchorTonnes: 1680,
    vehicles: 118,
    serviceLevel: 88,
    modes: [
      {
        mode: "road",
        label: "Dry van return slots",
        capacity: 1780,
        available: 58,
        status: "Moderate return density",
      },
      {
        mode: "air",
        label: "Mumbai air uplift",
        capacity: 80,
        available: 30,
        status: "High-value parcels",
      },
      {
        mode: "sea",
        label: "Nhava Sheva gateway",
        capacity: 520,
        available: 25,
        status: "Export consolidation",
      },
      {
        mode: "staging",
        label: "Jaipur rest-and-sort",
        capacity: 260,
        available: 49,
        status: "Urban consolidation",
      },
    ],
    shipments: [
      {
        id: "WE-01",
        shipper: "Marble Cluster",
        cargo: "Cut stone samples",
        origin: "Kishangarh",
        destination: "Mumbai",
        tonnes: 420,
        mode: "road",
        revenuePerTon: 3900,
        detourKm: 52,
        reliability: 90,
        compatibility: "dry",
        window: "60 h",
        urgency: 58,
      },
      {
        id: "WE-02",
        shipper: "Desert Foods",
        cargo: "Spice cartons",
        origin: "Jodhpur",
        destination: "Pune",
        tonnes: 280,
        mode: "road",
        revenuePerTon: 4700,
        detourKm: 38,
        reliability: 93,
        compatibility: "ambient",
        window: "48 h",
        urgency: 70,
      },
      {
        id: "WE-03",
        shipper: "Gem Export House",
        cargo: "Secured jewellery consignments",
        origin: "Jaipur",
        destination: "Mumbai airport",
        tonnes: 24,
        mode: "air",
        revenuePerTon: 28500,
        detourKm: 12,
        reliability: 96,
        compatibility: "regulated",
        window: "12 h",
        urgency: 99,
      },
      {
        id: "WE-04",
        shipper: "Textile Mills Association",
        cargo: "Home textile bales",
        origin: "Bhilwara",
        destination: "Chennai",
        tonnes: 360,
        mode: "sea",
        revenuePerTon: 3200,
        detourKm: 94,
        reliability: 84,
        compatibility: "dry",
        window: "6 d",
        urgency: 34,
      },
    ],
  },
  {
    id: "coastal",
    name: "Coastal Export Relay",
    anchor: "Britannia Chennai to Kerala replenishment",
    origin: "Chennai",
    destination: "Kochi + Calicut",
    returnLane: "Kerala to Tamil Nadu and export ports",
    recurring: "5 dispatch waves per week",
    distanceKm: 720,
    baselineEmptyKm: 43000,
    baseAnchorTonnes: 1320,
    vehicles: 94,
    serviceLevel: 93,
    modes: [
      {
        mode: "road",
        label: "Coastal truck return slots",
        capacity: 1440,
        available: 46,
        status: "Predictable short-haul loop",
      },
      {
        mode: "air",
        label: "Kochi air cargo",
        capacity: 74,
        available: 34,
        status: "Perishable and urgent uplift",
      },
      {
        mode: "sea",
        label: "Cochin export feeder",
        capacity: 610,
        available: 44,
        status: "Container export flow",
      },
      {
        mode: "staging",
        label: "Kochi warehouse buffer",
        capacity: 340,
        available: 58,
        status: "Multi-shipper staging",
      },
    ],
    shipments: [
      {
        id: "CE-01",
        shipper: "Kerala Coir Board",
        cargo: "Coir and matting exports",
        origin: "Alappuzha",
        destination: "Chennai port",
        tonnes: 390,
        mode: "sea",
        revenuePerTon: 3000,
        detourKm: 44,
        reliability: 87,
        compatibility: "dry",
        window: "5 d",
        urgency: 40,
      },
      {
        id: "CE-02",
        shipper: "Spice Valley",
        cargo: "Pepper and cardamom cartons",
        origin: "Kochi",
        destination: "Chennai",
        tonnes: 260,
        mode: "road",
        revenuePerTon: 5100,
        detourKm: 22,
        reliability: 92,
        compatibility: "ambient",
        window: "36 h",
        urgency: 74,
      },
      {
        id: "CE-03",
        shipper: "MedServe South",
        cargo: "Medical devices",
        origin: "Calicut",
        destination: "Bengaluru airport",
        tonnes: 36,
        mode: "air",
        revenuePerTon: 19000,
        detourKm: 68,
        reliability: 95,
        compatibility: "regulated",
        window: "16 h",
        urgency: 97,
      },
      {
        id: "CE-04",
        shipper: "Retail Returns Hub",
        cargo: "E-commerce reverse parcels",
        origin: "Kochi",
        destination: "Hyderabad",
        tonnes: 210,
        mode: "staging",
        revenuePerTon: 5600,
        detourKm: 86,
        reliability: 83,
        compatibility: "ambient",
        window: "84 h",
        urgency: 48,
      },
    ],
  },
];

const retailProfiles = [
  {
    id: "africa",
    name: "African Routes",
    terminal: "International departures pier B",
    passengerMix: "Traders, students, VFR, cultural tourism",
    weeklyFlights: 32,
    baseRevenue: 18200000,
    compliance: "Alcohol secondary, handicraft-led mix",
    assortments: [
      { label: "Indian and African handicrafts", share: 30, uplift: 18 },
      { label: "Tea, coffee and sweets gifting", share: 24, uplift: 14 },
      { label: "Durable snacks", share: 18, uplift: 9 },
      { label: "Travel electronics", share: 15, uplift: 7 },
      { label: "Beauty and wellness", share: 13, uplift: 6 },
    ],
  },
  {
    id: "uk",
    name: "UK Routes",
    terminal: "Premium duty-paid corridor",
    passengerMix: "Business, diaspora, leisure, premium gifting",
    weeklyFlights: 46,
    baseRevenue: 26400000,
    compliance: "Premium spirits where legally permitted",
    assortments: [
      { label: "Premium Indian spirits", share: 26, uplift: 20 },
      { label: "Luxury sweets and bakery gifting", share: 22, uplift: 13 },
      { label: "Tea, coffee and wellness", share: 20, uplift: 11 },
      { label: "Designer craft", share: 17, uplift: 8 },
      { label: "Travel essentials", share: 15, uplift: 5 },
    ],
  },
  {
    id: "saudi",
    name: "Saudi Routes",
    terminal: "Family and pilgrimage retail zone",
    passengerMix: "Pilgrimage, family travel, workers, gifting",
    weeklyFlights: 58,
    baseRevenue: 23900000,
    compliance: "Destination-appropriate non-liquor mix",
    assortments: [
      { label: "Dates, sweets and bakery gifting", share: 28, uplift: 16 },
      { label: "Fragrance and personal care", share: 24, uplift: 12 },
      { label: "Modest fashion accessories", share: 18, uplift: 8 },
      { label: "Travel health essentials", share: 17, uplift: 7 },
      { label: "Prayer and family travel items", share: 13, uplift: 6 },
    ],
  },
] satisfies RetailProfile[];

const formatCurrency = (amount: number) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);

const formatShortCurrency = (amount: number) => {
  if (amount >= 10000000) {
    return `${formatCurrency(amount / 10000000).replace(".00", "")} Cr`;
  }

  return `${formatCurrency(amount / 100000).replace(".00", "")} L`;
};

function scoreShipment(
  shipment: Shipment,
  maxDetour: number,
  guardrail: number,
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

function optimizeCorridor(
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
      reason:
        matchedTonnes === shipment.tonnes
          ? "Full match"
          : `${matchedTonnes} t partial match`,
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

export default function Home() {
  const [view, setView] = useState<"network" | "retail">("network");
  const [selectedCorridorId, setSelectedCorridorId] = useState<CorridorId>(
    initialNetworkInputs.corridorId,
  );
  const [anchorEnabled, setAnchorEnabled] = useState(initialNetworkInputs.anchorEnabled);
  const [anchorMultiplier, setAnchorMultiplier] = useState(initialNetworkInputs.anchorMultiplier);
  const [maxDetour, setMaxDetour] = useState(initialNetworkInputs.maxDetour);
  const [guardrail, setGuardrail] = useState(initialNetworkInputs.guardrail);
  const [appliedNetworkInputs, setAppliedNetworkInputs] =
    useState<NetworkInputs>(initialNetworkInputs);
  const [selectedRetailId, setSelectedRetailId] = useState<RetailId>("africa");
  const [passengerWave, setPassengerWave] = useState(62);
  const [corridorData, setCorridorData] = useState<Corridor[]>(corridors);
  const [retailData, setRetailData] = useState<RetailProfile[]>(retailProfiles);
  const [backendSummary, setBackendSummary] = useState<BackendSummary | null>(null);
  const [dataSource, setDataSource] = useState<DataSource>("loading");
  const [backendOptimization, setBackendOptimization] = useState<OptimizationResult | null>(null);
  const [optimizationSource, setOptimizationSource] =
    useState<OptimizationSource>("browser-fallback");

  useEffect(() => {
    let active = true;

    async function loadBackendData() {
      try {
        const [corridorResponse, retailResponse, healthResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/api/corridors`),
          fetch(`${API_BASE_URL}/api/retail-profiles`),
          fetch(`${API_BASE_URL}/api/health`),
        ]);

        if (!corridorResponse.ok || !retailResponse.ok || !healthResponse.ok) {
          throw new Error("Backend did not return healthy responses");
        }

        const [loadedCorridors, loadedRetailProfiles, health] = (await Promise.all([
          corridorResponse.json(),
          retailResponse.json(),
          healthResponse.json(),
        ])) as [Corridor[], RetailProfile[], { dataset: BackendSummary }];

        if (!active) {
          return;
        }

        if (loadedCorridors.length) {
          setCorridorData(loadedCorridors);
          setSelectedCorridorId((current) =>
            loadedCorridors.some((item) => item.id === current)
              ? current
              : loadedCorridors[0].id,
          );
          setAppliedNetworkInputs((current) =>
            loadedCorridors.some((item) => item.id === current.corridorId)
              ? current
              : { ...current, corridorId: loadedCorridors[0].id },
          );
        }

        if (loadedRetailProfiles.length) {
          setRetailData(loadedRetailProfiles);
          setSelectedRetailId((current) =>
            loadedRetailProfiles.some((item) => item.id === current)
              ? current
              : loadedRetailProfiles[0].id,
          );
        }

        setBackendSummary(health.dataset);
        setDataSource("backend");
      } catch {
        if (active) {
          setDataSource("fallback");
        }
      }
    }

    loadBackendData();

    return () => {
      active = false;
    };
  }, []);

  const draftNetworkInputs = useMemo(
    () => ({
      corridorId: selectedCorridorId,
      anchorEnabled,
      anchorMultiplier,
      maxDetour,
      guardrail,
    }),
    [selectedCorridorId, anchorEnabled, anchorMultiplier, maxDetour, guardrail],
  );
  const hasPendingNetworkInputs = !sameNetworkInputs(draftNetworkInputs, appliedNetworkInputs);
  const draftCorridor = corridorData.find((item) => item.id === selectedCorridorId) ?? corridorData[0];
  const corridor = corridorData.find((item) => item.id === appliedNetworkInputs.corridorId) ?? draftCorridor;
  const fallbackOptimization = useMemo(
    () =>
      optimizeCorridor(
        corridor,
        appliedNetworkInputs.anchorEnabled,
        appliedNetworkInputs.anchorMultiplier,
        appliedNetworkInputs.maxDetour,
        appliedNetworkInputs.guardrail,
      ),
    [corridor, appliedNetworkInputs],
  );
  const optimization = backendOptimization ?? fallbackOptimization;

  useEffect(() => {
    let active = true;

    async function loadBackendOptimization() {
      await Promise.resolve();

      if (!active) {
        return;
      }

      if (dataSource !== "backend") {
        setBackendOptimization(null);
        setOptimizationSource(dataSource === "loading" ? "loading" : "browser-fallback");
        return;
      }

      setBackendOptimization(null);
      setOptimizationSource("loading");

      try {
        const response = await fetch(`${API_BASE_URL}/api/optimise`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            corridorId: appliedNetworkInputs.corridorId,
            anchorEnabled: appliedNetworkInputs.anchorEnabled,
            anchorMultiplier: appliedNetworkInputs.anchorMultiplier,
            maxDetour: appliedNetworkInputs.maxDetour,
            guardrail: appliedNetworkInputs.guardrail,
          }),
        });

        if (!response.ok) {
          throw new Error("Backend optimiser did not return a successful response");
        }

        const payload = (await response.json()) as { result: OptimizationResult };

        if (active) {
          setBackendOptimization(payload.result);
          setOptimizationSource("backend");
        }
      } catch {
        if (active) {
          setBackendOptimization(null);
          setOptimizationSource("browser-fallback");
        }
      }
    }

    loadBackendOptimization();

    return () => {
      active = false;
    };
  }, [
    dataSource,
    appliedNetworkInputs,
  ]);

  const retail = retailData.find((item) => item.id === selectedRetailId) ?? retailData[0];
  const retailUplift = Math.round(
    retail.assortments.reduce((sum, item) => sum + item.uplift * (item.share / 100), 0) +
      passengerWave / 10,
  );
  const retailRevenue = Math.round(retail.baseRevenue * (1 + retailUplift / 100));
  const totalCapacity = corridor.modes.reduce((sum, item) => sum + item.capacity, 0);
  const modeUtilization = corridor.modes.map((item) => {
    const backendMode = optimization.modeUtilisation?.find((mode) => mode.mode === item.mode);
    const available =
      backendMode?.availableTonnes ??
      Math.round(
        item.capacity *
          (item.available / 100) *
          (appliedNetworkInputs.anchorEnabled ? appliedNetworkInputs.anchorMultiplier : 0.54),
      );
    const remaining = backendMode?.remainingTonnes ?? optimization.remaining[item.mode] ?? 0;
    const used = backendMode?.usedTonnes ?? Math.max(0, available - remaining);
    const utilization = backendMode?.utilisation ?? (available ? Math.round((used / available) * 100) : 0);

    return { ...item, available, remaining, used, utilization };
  });

  return (
    <main className="app-shell">
      <header className="command-bar">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true">
            <Route size={22} />
          </div>
          <div>
            <p className="eyebrow">CapacityIQ</p>
            <h1>Multimodal Freight Optimiser</h1>
          </div>
        </div>

        <div className="topline-status" aria-label="Current network status">
          <span>
            <CheckCircle2 size={16} />
            {appliedNetworkInputs.anchorEnabled
              ? "Britannia anchor demand active"
              : "Anchor demand reduced"}
          </span>
          <span>
            <Gauge size={16} />
            {optimization.loadFactor}% return load factor
          </span>
          <span>
            <Database size={16} />
            {dataSource === "backend" && backendSummary
              ? `${backendSummary.shipments.toLocaleString("en-IN")} CSV shipments`
              : dataSource === "loading"
                ? "Connecting CSV backend"
                : "Sample fallback data"}
          </span>
          <span>
            <RefreshCw size={16} />
            {optimizationSource === "backend"
              ? "Backend optimiser active"
              : optimizationSource === "loading"
                ? "Calling /api/optimise"
                : "Browser fallback optimiser"}
          </span>
        </div>

        <div className="view-switch" role="tablist" aria-label="Application view">
          <button
            type="button"
            className={view === "network" ? "is-active" : ""}
            onClick={() => setView("network")}
            role="tab"
            aria-selected={view === "network"}
          >
            <Truck size={16} />
            Freight
          </button>
          <button
            type="button"
            className={view === "retail" ? "is-active" : ""}
            onClick={() => setView("retail")}
            role="tab"
            aria-selected={view === "retail"}
          >
            <ShoppingBag size={16} />
            Airport retail
          </button>
        </div>
      </header>

      {view === "network" ? (
        <section className="workspace-grid" aria-label="Freight optimisation workspace">
          <aside className="panel control-panel" aria-label="Network controls">
            <div className="section-title">
              <SlidersHorizontal size={18} />
              <h2>Network Inputs</h2>
            </div>

            <div className="corridor-list" aria-label="Corridor selector">
              {corridorData.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className={selectedCorridorId === item.id ? "corridor-row is-selected" : "corridor-row"}
                  onClick={() => setSelectedCorridorId(item.id)}
                >
                  <span>{item.name}</span>
                  <small>{item.returnLane}</small>
                </button>
              ))}
            </div>

            <label className="toggle-row">
              <span>
                <strong>Britannia anchor</strong>
                <small>{draftCorridor.anchor}</small>
              </span>
              <input
                type="checkbox"
                checked={anchorEnabled}
                onChange={(event) => setAnchorEnabled(event.target.checked)}
              />
            </label>

            <div className="slider-group">
              <label htmlFor="anchor-volume">
                Anchor volume
                <span>{Math.round(anchorMultiplier * 100)}%</span>
              </label>
              <input
                id="anchor-volume"
                type="range"
                min="60"
                max="135"
                value={Math.round(anchorMultiplier * 100)}
                onChange={(event) => setAnchorMultiplier(Number(event.target.value) / 100)}
              />
            </div>

            <div className="slider-group">
              <label htmlFor="detour">
                Max detour
                <span>{maxDetour} km</span>
              </label>
              <input
                id="detour"
                type="range"
                min="40"
                max="220"
                value={maxDetour}
                onChange={(event) => setMaxDetour(Number(event.target.value))}
              />
            </div>

            <div className="slider-group">
              <label htmlFor="guardrail">
                Compatibility guardrail
                <span>{guardrail}%</span>
              </label>
              <input
                id="guardrail"
                type="range"
                min="50"
                max="92"
                value={guardrail}
                onChange={(event) => setGuardrail(Number(event.target.value))}
              />
            </div>

            <button
              type="button"
              className="primary-action"
              onClick={() => setAppliedNetworkInputs(draftNetworkInputs)}
              disabled={!hasPendingNetworkInputs}
            >
              <RefreshCw size={17} />
              {hasPendingNetworkInputs ? "Run optimiser" : "Optimiser current"}
            </button>
          </aside>

          <section className="main-board" aria-label="Corridor optimisation">
            <div className="kpi-grid">
              <Metric
                icon={ArrowRightLeft}
                label="Empty km avoided"
                value={optimization.emptyKmAvoided.toLocaleString("en-IN")}
                delta={`${Math.round((optimization.emptyKmAvoided / corridor.baselineEmptyKm) * 100)}% of exposed km`}
              />
              <Metric
                icon={PackageCheck}
                label="Matched cargo"
                value={`${optimization.matchedTonnes.toLocaleString("en-IN")} t`}
                delta={`${optimization.accepted.length} live shipper matches`}
              />
              <Metric
                icon={CircleDollarSign}
                label="Revenue unlocked"
                value={formatShortCurrency(optimization.revenue)}
                delta={`${formatShortCurrency(optimization.costSaved)} operating cost avoided`}
              />
              <Metric
                icon={TrendingUp}
                label="Unit cost drop"
                value={`${optimization.unitCostDrop}%`}
                delta="No proportional CAPEX increase"
              />
            </div>

            <div className="panel route-panel">
              <div className="route-copy">
                <p className="eyebrow">Live corridor</p>
                <h2>{corridor.name}</h2>
                <div className="lane-meta">
                  <span>{corridor.origin}</span>
                  <ArrowRightLeft size={16} />
                  <span>{corridor.destination}</span>
                </div>
              </div>

              <div className="route-map" aria-label={`${corridor.name} capacity route`}>
                <div className="route-line primary-line" />
                <div className="route-line return-line" />
                <div className="route-node origin-node">
                  <span>{corridor.origin}</span>
                </div>
                <div className="route-node hub-node">
                  <span>Staging hub</span>
                </div>
                <div className="route-node destination-node">
                  <span>{corridor.destination}</span>
                </div>
                <div className="moving-unit truck-unit" aria-hidden="true">
                  <Truck size={22} />
                </div>
                <div className="moving-unit plane-unit" aria-hidden="true">
                  <Plane size={20} />
                </div>
                <div className="moving-unit ship-unit" aria-hidden="true">
                  <Ship size={20} />
                </div>
              </div>

              <div className="route-facts">
                <span>
                  <Clock3 size={15} />
                  {corridor.recurring}
                </span>
                <span>
                  <ShieldCheck size={15} />
                  {corridor.serviceLevel}% service reliability
                </span>
                <span>
                  <Box size={15} />
                  {optimization.anchorTonnes.toLocaleString("en-IN")} t anchor volume
                </span>
              </div>
            </div>

            <div className="panel matches-panel">
              <div className="section-title">
                <PackageCheck size={18} />
                <h2>Recommended Matches</h2>
              </div>

              <div className="match-list">
                {optimization.accepted.slice(0, 8).map((match) => {
                  const ModeIcon = modeMeta[match.mode].Icon;

                  return (
                    <article className="match-row" key={match.id}>
                      <div className={`mode-chip ${modeMeta[match.mode].className}`}>
                        <ModeIcon size={16} />
                        {modeMeta[match.mode].label}
                      </div>
                      <div className="match-main">
                        <strong>{match.shipper}</strong>
                        <span>{match.cargo}</span>
                        <small>
                          {match.origin} to {match.destination}
                        </small>
                      </div>
                      <div className="match-score">
                        <strong>{match.score}</strong>
                        <span>score</span>
                      </div>
                      <div className="match-economics">
                        <strong>{match.matchedTonnes} t</strong>
                        <span>{formatCurrency(match.matchedTonnes * match.revenuePerTon)}</span>
                      </div>
                    </article>
                  );
                })}
              </div>
              {optimization.accepted.length > 8 ? (
                <p className="list-note">
                  Showing top 8 of {optimization.accepted.length.toLocaleString("en-IN")} accepted matches from the
                  active dataset.
                </p>
              ) : null}
            </div>
          </section>

          <aside className="right-rail" aria-label="Capacity and governance">
            <section className="panel capacity-panel">
              <div className="section-title">
                <Gauge size={18} />
                <h2>Capacity Inventory</h2>
              </div>

              <div className="capacity-stack">
                {modeUtilization.map((item) => {
                  const ModeIcon = modeMeta[item.mode].Icon;

                  return (
                    <div className="capacity-row" key={item.mode}>
                      <div className="capacity-heading">
                        <span>
                          <ModeIcon size={16} />
                          {item.label}
                        </span>
                        <strong>{item.utilization}%</strong>
                      </div>
                      <div className="bar-track" aria-hidden="true">
                        <span
                          className={`bar-fill ${modeMeta[item.mode].className}`}
                          style={{ width: `${Math.min(item.utilization, 100)}%` }}
                        />
                      </div>
                      <small>
                        {item.used} t matched of {item.available} t available
                      </small>
                    </div>
                  );
                })}
              </div>
            </section>

            <section className="panel economics-panel">
              <div className="section-title">
                <CircleDollarSign size={18} />
                <h2>Economic Case</h2>
              </div>
              <dl className="economics-list">
                <div>
                  <dt>Existing capacity scanned</dt>
                  <dd>{totalCapacity.toLocaleString("en-IN")} t</dd>
                </div>
                <div>
                  <dt>Transporter revenue</dt>
                  <dd>{formatCurrency(optimization.revenue)}</dd>
                </div>
                <div>
                  <dt>Cost avoided</dt>
                  <dd>{formatCurrency(optimization.costSaved)}</dd>
                </div>
                <div>
                  <dt>CAPEX required</dt>
                  <dd>0 new fleet assets</dd>
                </div>
              </dl>
            </section>

            <section className="panel exceptions-panel">
              <div className="section-title">
                <ShieldCheck size={18} />
                <h2>Guardrail Queue</h2>
              </div>
              <div className="exception-list">
                {optimization.declined.slice(0, 4).map((item) => (
                  <div className="exception-row" key={item.id}>
                    <XCircle size={16} />
                    <span>
                      <strong>{item.cargo}</strong>
                      <small>{item.reason}</small>
                    </span>
                  </div>
                ))}
              </div>
            </section>
          </aside>
        </section>
      ) : (
        <section className="retail-grid" aria-label="Airport retail optimisation workspace">
          <aside className="panel control-panel" aria-label="Retail route controls">
            <div className="section-title">
              <ShoppingBag size={18} />
              <h2>Route Clusters</h2>
            </div>

            <div className="corridor-list">
              {retailData.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className={selectedRetailId === item.id ? "corridor-row is-selected" : "corridor-row"}
                  onClick={() => setSelectedRetailId(item.id)}
                >
                  <span>{item.name}</span>
                  <small>{item.passengerMix}</small>
                </button>
              ))}
            </div>

            <div className="slider-group">
              <label htmlFor="passenger-wave">
                Passenger signal
                <span>{passengerWave}%</span>
              </label>
              <input
                id="passenger-wave"
                type="range"
                min="20"
                max="95"
                value={passengerWave}
                onChange={(event) => setPassengerWave(Number(event.target.value))}
              />
            </div>

            <div className="retail-note">
              <ShieldCheck size={18} />
              <span>{retail.compliance}</span>
            </div>
          </aside>

          <section className="panel retail-board">
            <div className="retail-header">
              <div>
                <p className="eyebrow">Airport optimisation</p>
                <h2>{retail.name}</h2>
                <p>{retail.terminal}</p>
              </div>
              <div className="retail-score">
                <strong>{retailUplift}%</strong>
                <span>sales uplift</span>
              </div>
            </div>

            <div className="store-layout" aria-label={`${retail.name} airport retail allocation`}>
              {retail.assortments.map((item, index) => (
                <div
                  key={item.label}
                  className={`store-zone zone-${index + 1}`}
                  style={{ flexBasis: `${Math.max(16, item.share)}%` }}
                >
                  <strong>{item.share}%</strong>
                  <span>{item.label}</span>
                </div>
              ))}
            </div>

            <div className="assortment-stack">
              {retail.assortments.map((item) => (
                <div className="assortment-row" key={item.label}>
                  <div className="capacity-heading">
                    <span>{item.label}</span>
                    <strong>+{item.uplift}%</strong>
                  </div>
                  <div className="bar-track" aria-hidden="true">
                    <span className="bar-fill retail-fill" style={{ width: `${item.share}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </section>

          <aside className="right-rail">
            <Metric
              icon={Plane}
              label="Weekly flights"
              value={retail.weeklyFlights.toString()}
              delta={retail.passengerMix}
            />
            <Metric
              icon={ShoppingBag}
              label="Optimised revenue"
              value={formatShortCurrency(retailRevenue)}
              delta={`${formatShortCurrency(retailRevenue - retail.baseRevenue)} incremental`}
            />
            <Metric
              icon={TrendingUp}
              label="Asset thesis"
              value="Same stores"
              delta="Higher revenue from existing airport retail infrastructure"
            />
          </aside>
        </section>
      )}
    </main>
  );
}

function Metric({
  icon: Icon,
  label,
  value,
  delta,
}: {
  icon: typeof Truck;
  label: string;
  value: string;
  delta: string;
}) {
  return (
    <article className="metric-card">
      <div className="metric-icon" aria-hidden="true">
        <Icon size={18} />
      </div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{delta}</small>
      </div>
    </article>
  );
}
