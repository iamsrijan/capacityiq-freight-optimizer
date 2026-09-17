import { Plane, Ship, Truck, Warehouse } from "lucide-react";

import type { MetricIcon, Mode } from "./types";

export const modeMeta = {
  road: { label: "Road", Icon: Truck, className: "mode-road" },
  air: { label: "Air", Icon: Plane, className: "mode-air" },
  sea: { label: "Sea", Icon: Ship, className: "mode-sea" },
  staging: { label: "Staging", Icon: Warehouse, className: "mode-staging" },
} satisfies Record<Mode, { label: string; Icon: MetricIcon; className: string }>;
