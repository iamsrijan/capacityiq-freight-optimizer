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
  XCircle,
} from "lucide-react";

import { Metric } from "./components/Metric";
import { corridors, retailProfiles } from "./data/fallback-data";
import { fetchBackendOptimization, fetchInitialDashboardData } from "./lib/api";
import { initialNetworkInputs, sameNetworkInputs } from "./lib/config";
import { formatCurrency, formatShortCurrency } from "./lib/formatters";
import { modeMeta } from "./lib/mode-meta";
import { optimizeCorridor } from "./lib/optimizer";
import type {
  BackendSummary,
  Corridor,
  CorridorId,
  DataSource,
  NetworkInputs,
  OptimizationResult,
  OptimizationSource,
  RetailId,
  RetailProfile,
} from "./lib/types";


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
        const {
          corridors: loadedCorridors,
          retailProfiles: loadedRetailProfiles,
          summary,
        } = await fetchInitialDashboardData();

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

        setBackendSummary(summary);
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

  // Draft inputs can move freely; applied inputs are the last set submitted to the optimiser.
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
        const result = await fetchBackendOptimization(appliedNetworkInputs);

        if (active) {
          setBackendOptimization(result);
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
  const recommendedActions = optimization.recommendedActions ?? [];

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

            <div className="panel action-panel">
              <div className="section-title">
                <Route size={18} />
                <h2>Action Recommendations</h2>
              </div>

              <div className="action-list">
                {recommendedActions.slice(0, 4).map((action) => {
                  const ModeIcon = modeMeta[action.mode].Icon;

                  return (
                    <article className="action-card" key={action.id}>
                      <div className="action-card-header">
                        <div className={`mode-chip ${modeMeta[action.mode].className}`}>
                          <ModeIcon size={16} />
                          {modeMeta[action.mode].label}
                        </div>
                        <div>
                          <strong>{action.headline}</strong>
                          <span>{action.shipper}</span>
                        </div>
                      </div>

                      <p>{action.operatingInstruction}</p>

                      <div className="action-route" aria-label={`Recommended route for ${action.cargo}`}>
                        {action.route.map((node, index) => (
                          <span className="route-step" key={`${action.id}-${node}`}>
                            {index > 0 ? <ArrowRightLeft size={13} /> : null}
                            {node}
                          </span>
                        ))}
                      </div>

                      <div className="action-impact">
                        <span>
                          <strong>{action.matchedTonnes.toLocaleString("en-IN")} t</strong>
                          quantity
                        </span>
                        <span>
                          <strong>{formatShortCurrency(action.revenue)}</strong>
                          revenue
                        </span>
                        <span>
                          <strong>{action.emptyKmAvoided.toLocaleString("en-IN")} km</strong>
                          empty km avoided
                        </span>
                        <span>
                          <strong>{action.capacityShare}%</strong>
                          mode capacity
                        </span>
                      </div>

                      <div className="action-why">
                        {action.why.slice(0, 3).map((reason) => (
                          <small key={reason}>{reason}</small>
                        ))}
                      </div>
                    </article>
                  );
                })}
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
