import rawDataset from "../data/site-dataset.json";
import type { AirCarrier, BackendSummary, Corridor, RetailProfile } from "./types";

export type SiteDataset = {
  corridors: Corridor[];
  retailProfiles: RetailProfile[];
  airCarriers: AirCarrier[];
  summary: BackendSummary;
};

// The deployment build bundles a deterministic snapshot of the CSV tables.
export const siteDataset = rawDataset as SiteDataset;

export function findSiteCorridor(corridorId: string) {
  return siteDataset.corridors.find((corridor) => corridor.id === corridorId);
}
