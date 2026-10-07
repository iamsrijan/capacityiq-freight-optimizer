# CapacityIQ Freight And Capacity Optimiser

CapacityIQ is a local full-stack prototype for an AI-powered freight and capacity optimisation marketplace. It demonstrates how shippers, transporters, air cargo capacity, sea freight capacity, and staging hubs can be matched so existing assets work harder before new assets are purchased.

The freight example uses Britannia as the anchor demand partner. Britannia creates predictable base movement into a corridor. The platform then looks for compatible third-party cargo that can use empty or underused return capacity. The same optimisation principle is also shown for airport retail, where passenger and route signals change product allocation inside existing shop space.

The core thesis is:

> Do not buy more assets first. Use existing assets more intelligently.

## Current App Shape

The application has two visible workspaces.

| Workspace | Purpose | Main Output |
| --- | --- | --- |
| Freight Optimisation | Match cargo demand with unused road, air, sea, and staging capacity | Empty kilometres avoided, matched cargo, unlocked revenue, load factor, recommended actions, and guardrail queue |
| Airport Retail Optimisation | Match product mix with passenger route demand | Product allocation, sales uplift, optimised revenue, and store productivity message |

K-means clustering is not shown as a separate tab anymore. It is now used inside the freight optimiser calculation itself. The optimiser groups similar shipments, calculates a cluster-fit signal, and uses that signal while scoring and ranking loads.

## Screenshots

### Freight Workspace

![Freight workspace](docs/screenshots/freight-workspace-annotated.jpg)

| Marker | Area | What It Does |
| --- | --- | --- |
| 1 | Workspace tabs | Switch between Freight and Airport retail views |
| 2 | Network inputs | Choose corridor, anchor demand, detour policy, driver quality, clearance cap, and guardrail strictness |
| 3 | Key result cards | Show empty kilometres avoided, matched cargo, revenue, and unit cost impact |
| 4 | Live corridor map | Show the selected corridor and multimodal movement pattern |
| 5 | Capacity and economics rail | Show mode utilisation, operating intelligence, savings, capacity, and review queue |

### Recommended Matches

![Freight matches](docs/screenshots/freight-matches-annotated.jpg)

| Marker | Area | What It Does |
| --- | --- | --- |
| 1 | Run optimiser | Applies the visible network inputs and requests a backend optimisation run |
| 2 | Recommended Matches | Shows the strongest cargo matches from the active dataset |
| 3 | Guardrail Queue | Shows shipments rejected or flagged for review |

### Airport Retail Workspace

![Airport retail workspace](docs/screenshots/airport-retail-workspace-annotated.jpg)

| Marker | Area | What It Does |
| --- | --- | --- |
| 1 | Passenger routes | Selects the passenger route profile |
| 2 | Passenger signal slider | Models stronger or weaker passenger demand |
| 3 | Product allocation board | Shows how store space should be assigned |
| 4 | Sales uplift | Shows expected uplift from better assortment matching |
| 5 | Retail metrics | Shows flights, revenue, and asset productivity |

## Detailed Walkthrough

### 1. Freight Optimisation

Use the Freight tab to simulate how the marketplace fills unused freight capacity. Start by selecting a corridor from the left panel. The selected corridor changes the route, shipment pool, available road/air/sea/staging capacity, and anchor assumptions.

| Control | Meaning | What Changes |
| --- | --- | --- |
| Corridor | Operating lane being analysed | Changes source/destination, shipment candidates, capacity, and route map |
| Britannia anchor | Whether predictable anchor demand is active | Enabled uses normal anchor factor; disabled reduces available network density |
| Anchor volume | Anchor demand multiplier | Higher values increase adjusted capacity and anchor tonnes |
| Max detour | Maximum non-air route deviation | Lower values reject more loads; higher values allow more flexible matching |
| Compatibility guardrail | Strictness for cargo fit and risk | Higher values reject risky cargo such as chilled/regulated loads more aggressively |
| Driver score floor | Minimum acceptable driver/handler quality | Low-score operators are sent to the Guardrail Queue |
| Air clearance cap | Maximum handling + security + customs + layover window | Air shipments breaching the cap are rejected |
| Prefer contracted capacity | Whether spot-market loads are penalised | Contracted or SLA capacity scores higher than spot capacity |

After changing inputs, select **Run optimiser**. The app sends the applied scenario to `/api/optimise`. The KPI cards update with empty kilometres avoided, matched tonnes, revenue unlocked, and unit cost reduction.

The Action Recommendations panel explains:

| Field | Meaning |
| --- | --- |
| Cargo and shipper | What product should move and who owns it |
| Mode | Whether it should move by road, air, sea, or staging |
| Route | The corridor-aware movement sequence |
| Quantity | The actual matched tonnes accepted into capacity |
| Vehicle profile | The kind of transport asset required |
| Driver score and contract | Operating quality assumptions |
| Cluster fit | K-means signal showing how well this shipment group fits the network |
| Why | Plain-language explanation of why the optimiser accepted the match |

The Guardrail Queue is not an error list. It is the list of loads the optimiser chose not to carry in this scenario because capacity, detour, driver score, clearance time, or compatibility did not clear the rules.

### 2. Airport Retail Optimisation

Use the Airport retail tab to show that the same optimisation idea applies outside freight. Instead of trucks and shipments, the app uses passenger-route profiles and product assortment.

Select a passenger route profile such as Africa, UK, Saudi, Domestic Metro, or North America. Then adjust Passenger signal to simulate stronger or weaker passenger demand.

The layout board changes the recommended product-space mix. The revenue card shows how better route-aware merchandising can increase revenue from the same airport shops without adding major CAPEX.

## New Features Added After The Last Presentation

These are the important upgrades added after your last presentation feedback.

| New Feature | What Changed | Demo Talking Point |
| --- | --- | --- |
| K-means inside freight scoring | K-means is now part of `/api/optimise`, not a separate tab | The AI model now affects shipment ranking and accepted matches |
| Two-tab UI | The visible app now keeps only Freight and Airport retail | The demo is cleaner and easier to explain |
| Cluster fit per recommendation | Each recommended action can show the shipment's K-means group and cluster-fit score | This explains why a load is operationally similar to other good matches |
| Cluster boosted count | Operational Intelligence shows how many accepted matches received a positive cluster adjustment | This proves clustering is being used in the actual calculation |
| Driver score floor | Freight inputs now include minimum driver/operator quality | Risky capacity can be filtered before accepting cargo |
| Air clearance cap | Air cargo is checked against handling, security, customs, and layover time | Airport cargo is treated differently from road cargo |
| Contracted capacity preference | Spot-market loads can be penalised when contracted capacity is preferred | The app can reflect SLA and reliability preferences |
| Realistic operating reserve | Capacity bars use bookable capacity plus reserve capacity | Capacity no longer unrealistically shows 100% simply because demand exists |
| Larger CSV-backed backend data | The backend works from thousands of shipment rows and partner/hub tables | The demo feels closer to a pilot dataset than a static mockup |
| Better action recommendations | Recommendations now include cargo, route, mode, vehicle, timing, driver, contract, and cluster reason | The app tells operators what to do, not only what the KPI is |

## How K-Means Is Used Now

K-means clustering is now an internal input to the freight optimiser.

The backend takes shipment rows from CSV and converts each shipment into a numeric vector:

| Feature | Meaning |
| --- | --- |
| `tonnes` | Shipment quantity |
| `revenuePerTon` | Commercial value of the load |
| `detourKm` | Route deviation required |
| `reliability` | Historical reliability signal |
| `urgency` | Time sensitivity |
| `cargoFit` | Compatibility with anchor freight and operating rules |
| `driverScore` | Quality of assigned driver/operator |
| `clearanceMinutes` | Handling + security + customs + layover time |

The clustering flow is:

```text
CSV shipment data
  -> standardise numeric features
  -> run deterministic K-means
  -> assign each shipment to a cluster
  -> calculate cluster centroid
  -> convert centroid into clusterFit
  -> convert clusterFit into clusterAdjustment
  -> add clusterAdjustment to shipment score
  -> allocate capacity from highest score downward
```

This means clustering is no longer a visual explanation only. It affects the actual optimisation result.

## Local Setup

Clone the project into any folder on your machine or server:

```bash
git clone https://github.com/Rump-Labs/RouteFlow.git
cd RouteFlow
```

Run the full local stack:

```bash
npm install
npm run dev
```

Then open:

```bash
http://localhost:3000/
```

The `npm run dev` command starts both:

| Service | URL | Purpose |
| --- | --- | --- |
| Frontend | `http://localhost:3000/` | React dashboard |
| Backend | `http://127.0.0.1:8000/` | CSV-backed API and optimiser |

## Why The Browser URL Stays On Port 3000

The browser address bar shows the frontend route, so it normally stays at:

```bash
http://localhost:3000/
```

That does not mean the backend is unused. The React app calls the backend in the background using `fetch()`. These API calls do not navigate the browser to a new page, so the address bar does not change.

When the backend is running, the top status bar shows:

```text
Backend optimiser active
```

The app uses these backend calls:

| Frontend Action | Backend Call |
| --- | --- |
| App loads | `GET http://127.0.0.1:8000/api/corridors` |
| App loads | `GET http://127.0.0.1:8000/api/retail-profiles` |
| App loads | `GET http://127.0.0.1:8000/api/health` |
| Select Run optimiser after changing freight inputs | `POST http://127.0.0.1:8000/api/optimise` |

You can also verify the backend directly:

```bash
curl http://127.0.0.1:8000/api/health
```

## Other Useful Commands

| Command | Purpose |
| --- | --- |
| `npm run dev` | Start backend and frontend together |
| `npm run dev:backend` | Start only the Python backend on port `8000` |
| `npm run dev:frontend -- --host localhost --port 3000` | Start only the frontend on port `3000` |
| `npm run seed:data` | Regenerate the dummy CSV dataset |
| `npm run test:backend` | Run backend dataset and optimiser tests |
| `npm run lint` | Run frontend lint checks |
| `npm run build` | Build the frontend |

## Technology Stack

| Layer | Language Or Tool | Why It Was Used |
| --- | --- | --- |
| Frontend UI | React 19 with TypeScript and TSX | Best fit for interactive dashboards with sliders, tabs, cards, and fast state updates |
| Frontend runtime | Vinext and Vite | Local development server, build pipeline, and fast refresh |
| Styling | CSS with Tailwind import | Full dashboard layout, responsive behaviour, cards, buttons, route map, and sliders |
| Icons | lucide-react | Clean interface icons for transport, metrics, controls, and retail |
| Backend API | Python standard library HTTP server | Easy to run locally without installing extra Python packages |
| AI segmentation | Deterministic K-means in Python and TypeScript fallback | Groups similar shipments and feeds cluster signals into optimiser scoring |
| Data storage | CSV files | Simple table format that business and data teams can inspect or replace |
| Package scripts | Node.js and npm | Single command workflow for local development and verification |

React and TypeScript are used for the visible application because this is a dashboard-heavy product. Python is used for the backend because optimisation, routing, forecasting, and data processing are natural Python workloads.

## Backend Dataset

The backend uses dummy CSV data in `backend/data`. The dataset is intentionally large enough to feel like a real pilot instead of a tiny mockup.

| CSV Table | Rows | Purpose |
| --- | ---: | --- |
| `corridors.csv` | 12 | Freight corridors and anchor movement assumptions |
| `capacity.csv` | 48 | Road, air, sea, and staging capacity by corridor |
| `shipments.csv` | 2,400 | Candidate cargo loads to match into available capacity |
| `hubs.csv` | 42 | Staging hubs, docks, cold capacity, and reliability |
| `partners.csv` | 144 | Transporters, air cargo partners, warehouses, and 3PLs |
| `retail_profiles.csv` | 8 | Airport passenger route profiles and revenue assumptions |
| `retail_assortments.csv` | 40 | Product allocation and uplift assumptions by passenger route profile |

Regenerate the dataset:

```bash
npm run seed:data
```

The seed script is deterministic, so the same command produces repeatable data.

## Backend API

Start the backend:

```bash
npm run dev:backend
```

Health check:

```bash
curl http://127.0.0.1:8000/api/health
```

### Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Service status, dataset counts, and available endpoints |
| `GET` | `/api/tables` | Row counts and total capacity across CSV tables |
| `GET` | `/api/corridors` | All corridors with nested capacity and shipment rows |
| `GET` | `/api/corridors/{id}` | One corridor with nested capacity and shipments |
| `GET` | `/api/shipments?corridor_id=northeast&limit=50` | Paginated shipment rows |
| `GET` | `/api/capacity?corridor_id=northeast` | Capacity rows for one or all corridors |
| `GET` | `/api/retail-profiles` | Airport retail route profiles and assortment rules |
| `GET` | `/api/hubs?limit=50` | Hub table rows |
| `GET` | `/api/partners?limit=50` | Partner table rows |
| `POST` | `/api/optimise` | Run the backend freight optimiser |
| `POST` | `/api/optimize` | Same as `/api/optimise` for US spelling |

### Optimiser Request Example

```bash
curl -X POST http://127.0.0.1:8000/api/optimise \
  -H 'Content-Type: application/json' \
  -d '{
    "corridorId": "northeast",
    "anchorEnabled": true,
    "anchorMultiplier": 1,
    "maxDetour": 120,
    "guardrail": 74,
    "minDriverScore": 72,
    "maxClearanceMinutes": 360,
    "preferContracted": true
  }'
```

### Optimiser Response Shape

| Field | Meaning |
| --- | --- |
| `accepted` | Shipments accepted into capacity |
| `declined` | Shipments rejected or queued for review |
| `recommendedActions` | Business-readable instructions showing what cargo to move, by which mode, through which route sequence, and why |
| `remaining` | Remaining tonnes by mode |
| `modeUtilisation` | Used, remaining, and utilisation by mode |
| `bookableTonnes` | Tonnes the optimiser is allowed to allocate after operating reserve |
| `reserveTonnes` | Capacity held back for service reliability, slot risk, and operational buffer |
| `operationalSummary` | Driver, route familiarity, contract, compatibility, air-clearance, and K-means cluster-fit summary |
| `clusterLabel` | Shipment group assigned by K-means |
| `clusterFit` | Cluster-level quality signal used in scoring |
| `clusterAdjustment` | Points added or subtracted from the shipment score because of its cluster |
| `matchedTonnes` | Total tonnes matched |
| `revenue` | Estimated revenue unlocked |
| `emptyKmAvoided` | Empty kilometres avoided |
| `costSaved` | Operating cost avoided |
| `loadFactor` | Return capacity load factor |
| `unitCostDrop` | Estimated freight unit cost reduction |
| `anchorTonnes` | Anchor demand volume used in the optimiser run |

## How The App Recommends Routes, Products, And Quantity

The app does not stop at KPI numbers. Each backend optimisation run also creates an Action Recommendations panel. This panel converts accepted shipment matches into plain operating instructions.

For every recommended move, the backend decides:

| Decision | How It Is Calculated |
| --- | --- |
| What product or cargo should move | Selects the accepted shipment with the best combination of K-means cluster fit, compatibility score, demand priority, revenue, detour feasibility, and available mode capacity |
| How much should move | Uses the matched tonnes actually accepted into bookable capacity after reserve capacity is held back |
| Which mode should carry it | Uses the shipment mode that passed capacity and guardrail checks: road, air, sea, or staging |
| Which route should be followed | Builds a corridor-aware route sequence from shipment origin, corridor nodes, and shipment destination |
| Why the recommendation is useful | Explains cluster fit, compatibility, revenue, empty kilometres avoided, and capacity share in simple language |

Example recommendation:

```text
Move 26 t of packaged food by road
Route: Dibrugarh -> Guwahati -> Siliguri -> Kolkata
Instruction: Assign this load to a return truck lane within the detour policy.
Why: Strong cluster fit, clear compatibility, meaningful revenue, and reduced empty kilometres.
```

## Optimiser Calculation Formulas

When the user selects Run optimiser, the frontend sends the active corridor and scenario inputs to `/api/optimise`. The backend calculates capacity, shipment scores, accepted matches, KPI cards, mode utilisation, and recommended actions with the formulas below.

### Scenario And Capacity

| Parameter | Formula |
| --- | --- |
| `anchorFactor` | `anchorMultiplier` when Britannia anchor is enabled, otherwise `0.54` |
| `availableCapacity` | `capacity * (availablePercent / 100) * anchorFactor` |
| `bookableCapacity` | `availableCapacity * modeTargetFill` |
| `reserveTonnes` | `availableCapacity - bookableCapacity` |

Mode target fill values keep a practical operating buffer instead of allowing every mode to show 100% utilisation.

| Mode | Target Fill |
| --- | ---: |
| `road` | `0.93` |
| `air` | `0.84` |
| `sea` | `0.78` |
| `staging` | `0.88` |

### Shipment Scoring

Each shipment receives a score before capacity is allocated.

| Component | Formula |
| --- | --- |
| `routeFit` | `max(0, 1 - detourKm / max(maxDetour, 1))` |
| `reliabilityFit` | `reliability / 100` |
| `revenueFit` | `min(revenuePerTon / 12000, 1)` |
| `urgencyFit` | `urgency / 100` |
| `compatibilityFit` | Value from the compatibility table below |
| `cargoFit` | Value from cargo-family compatibility: food-grade dry scores highest, regulated or secured cargo scores lower unless handled separately |
| `driverFit` | `driverScore / 100` |
| `routeFamiliarityFit` | `min(routeFamiliarityTrips / 50, 1)` |
| `contractFit` | Contract strength value: dedicated/fixed/SLA capacity scores above spot-market capacity |
| `scheduleFit` | `1` for simple non-air moves; for air or regulated moves it reduces when handling + security + customs + layover exceeds the clearance cap |
| `clusterFit` | Weighted score from the K-means shipment-cluster centroid |
| `clusterAdjustment` | `round((clusterFit - 0.66) * 24)` |
| `guardrailPenalty` | `((guardrail - 50) / 50) * (1 - compatibilityFit) * 22` |
| `driverPenalty` | `max(0, minDriverScore - driverScore) * 0.35` |
| `contractPenalty` | `5` when contracted capacity is preferred and the shipment is spot-market, otherwise `0` |
| `clearancePenalty` | `max(0, clearanceMinutes - maxClearanceMinutes) / 60 * 4` |
| `score` | `round(routeFit * 22 + reliabilityFit * 17 + compatibilityFit * 13 + cargoFit * 12 + revenueFit * 10 + urgencyFit * 6 + driverFit * 8 + routeFamiliarityFit * 6 + contractFit * 4 + scheduleFit * 2 + clusterAdjustment - guardrailPenalty - driverPenalty - contractPenalty - clearancePenalty)` |

Compatibility fit values:

| Cargo Compatibility | Fit Value |
| --- | ---: |
| `ambient` | `1.00` |
| `dry` | `1.00` |
| `fragile` | `0.86` |
| `regulated` | `0.74` |
| `chilled` | `0.42` |

### K-Means Cluster Fit Formula

The shipment cluster centroid is converted into a score using:

```text
clusterFit =
  revenueComponent * 0.16
  + reliabilityComponent * 0.18
  + urgencyComponent * 0.10
  + cargoComponent * 0.22
  + driverComponent * 0.14
  + detourComponent * 0.10
  + clearanceComponent * 0.10
```

Where:

| Component | Formula |
| --- | --- |
| `revenueComponent` | `min(clusterRevenuePerTon / 16000, 1)` |
| `reliabilityComponent` | `clusterReliability / 100` |
| `urgencyComponent` | `clusterUrgency / 100` |
| `cargoComponent` | `clusterCargoFit` |
| `driverComponent` | `clusterDriverScore / 100` |
| `detourComponent` | `max(0, 1 - clusterDetourKm / 220)` |
| `clearanceComponent` | `max(0, 1 - clusterClearanceMinutes / 720)` |

### Acceptance Rules

| Rule | Formula Or Condition |
| --- | --- |
| Minimum acceptance score | `threshold = max(55, guardrail - 12)` |
| Capacity check | Reject if no bookable capacity remains in the shipment mode |
| Detour check | Reject non-air shipments when `detourKm > maxDetour` |
| Driver check | Reject when `driverScore < minDriverScore` |
| Air clearance check | Reject air shipments when `handlingMinutes + securityMinutes + customsMinutes + layoverMinutes > maxClearanceMinutes` |
| Cargo segregation check | Reject lower-fit cargo families when strict guardrails are active |
| Score check | Reject when `score < threshold` |
| Strict guardrail check | Reject `chilled` or `regulated` cargo when `guardrail >= 82` |

Accepted shipments are processed from highest score to lowest score. A shipment can be fully matched or partially matched depending on the bookable capacity left in its mode.

### Allocation And KPI Cards

| Output | Formula |
| --- | --- |
| `matchedTonnes` per shipment | `min(shipmentTonnes, remainingBookableCapacityForMode)` |
| `adjustedCapacity` | `sum(availableCapacity across all modes)` |
| `totalMatchedTonnes` | `sum(matchedTonnes for accepted shipments)` |
| `revenue` | `sum(matchedTonnes * revenuePerTon)` |
| `emptyKmAvoided` | `round(sum((matchedTonnes / vehicleEquivalentTonnes) * max(120, distanceKm - detourKm)))` |
| `vehicleEquivalentTonnes` | `16` for road, `24` for air, sea, or staging |
| `costSaved` | `emptyKmAvoided * 68` |
| `loadFactor` | `round(totalMatchedTonnes / adjustedCapacity * 100)` |
| `baselineLoadFactor` | `19` when anchor is enabled, otherwise `11` |
| `unitCostDrop` | `max(0, min(34, round((loadFactor - baselineLoadFactor) * 0.62)))` |
| `anchorTonnes` | `round(baseAnchorTonnes * anchorFactor)` |

### Mode Utilisation

| Output | Formula |
| --- | --- |
| `usedTonnes` | `bookableCapacity - remainingBookableCapacity` |
| `remainingTonnes` | `availableCapacity - usedTonnes` |
| `reserveTonnes` | `availableCapacity - bookableCapacity` |
| `utilisation` | `round(usedTonnes / availableCapacity * 100)` |

### Operational Intelligence Summary

| Output | Formula |
| --- | --- |
| `avgDriverScore` | Average driver score across accepted matches |
| `avgRouteFamiliarityTrips` | Average previous trips on similar routes across accepted matches |
| `contractedShare` | Accepted non-spot-market matches / accepted matches |
| `compatibilityCleared` | Accepted matches without strict cargo segregation flags / accepted matches |
| `airClearanceBreaches` | Count of declined air shipments exceeding the clearance cap |
| `avgMonthlyCost` | Average historical monthly cost across accepted matches |
| `avgClusterFit` | Average K-means cluster fit across accepted matches |
| `clusterBoostedMatches` | Count of accepted matches where K-means added positive score points |

## Frontend Data Flow

The frontend starts with embedded sample data so the app can still open if the backend is not running. When the backend is available, the app fetches:

1. `/api/corridors`
2. `/api/retail-profiles`
3. `/api/health`

After loading succeeds, the top status bar shows the CSV shipment count. Freight controls act as draft network inputs. When the user selects Run optimiser, the frontend posts the visible corridor, anchor, detour, guardrail, driver score floor, air clearance cap, and contracted-capacity preference to `/api/optimise`. The backend returns the displayed accepted matches, rejected queue, mode utilisation, revenue, empty kilometres avoided, cost saved, load factor, unit cost impact, operational intelligence summary, and action-level vehicle/driver/contract/schedule/K-means recommendations.

If backend loading or backend optimisation fails, the app displays fallback status text and continues to work with the smaller embedded browser-side optimiser. The browser fallback also runs a deterministic K-means pass over the fallback shipment data.

Capacity Inventory bars show matched tonnes against operationally available capacity. The backend also keeps mode-specific reserves, so road, air, sea, and staging do not automatically show 100% utilisation just because demand exists.

## Project Architecture

```text
capacityiq-freight-optimizer/
  app/
    page.tsx              Frontend screen orchestration and two-tab layout
    components/
      Metric.tsx          Reusable KPI card component
    data/
      fallback-data.ts    Browser fallback corridors and retail profiles
    lib/
      api.ts              Backend API client functions
      config.ts           Frontend constants and initial network inputs
      formatters.ts       Currency and short-number formatting helpers
      mode-meta.ts        Mode labels, icons, and CSS class names
      optimizer.ts        Browser fallback optimiser with K-means shipment clustering
      types.ts            Shared frontend domain types
    layout.tsx            Root app shell and metadata
    globals.css           Dashboard styling and responsive layout
  backend/
    config.py             Backend constants, endpoints, and mode reserve settings
    clustering.py         Deterministic K-means helpers and shipment cluster lookup
    repository.py         CSV loading and dataset lookup functions
    optimizer.py          Freight scoring, K-means score adjustment, and capacity allocation logic
    server.py             Thin local HTTP API entrypoint
    utils.py              Parsing, pagination, and numeric conversion helpers
    test_api.py           Backend tests
    data/
      corridors.csv
      capacity.csv
      shipments.csv
      hubs.csv
      partners.csv
      retail_profiles.csv
      retail_assortments.csv
  docs/
    screenshots/          Annotated screenshots used in this README
  scripts/
    seed_dummy_data.py    Deterministic dummy data generator
    start-local.sh        Starts backend and frontend together
  package.json            npm scripts and frontend dependencies
  vite.config.ts          Frontend build and local dev configuration
  tsconfig.json           TypeScript configuration
```

## Function Call Mapping

### Frontend Functions

| Function Or Object | File | Called By | Purpose |
| --- | --- | --- | --- |
| `Home` | `app/page.tsx` | React page runtime | Owns screen state, loads backend data, chooses Freight or Airport retail view, and renders the dashboard |
| `useEffect(loadBackendData)` | `app/page.tsx` | `Home` | Calls `fetchInitialDashboardData` and stores loaded CSV-backed data |
| `useEffect(loadBackendOptimization)` | `app/page.tsx` | `Home` | Calls `fetchBackendOptimization` for the applied freight inputs |
| `fetchInitialDashboardData` | `app/lib/api.ts` | `Home` | Fetches corridors, retail profiles, and dataset health |
| `fetchBackendOptimization` | `app/lib/api.ts` | `Home` | Posts the applied freight inputs to `/api/optimise` |
| `buildShipmentClusterLookup` | `app/lib/optimizer.ts` | `optimizeCorridor` | Browser fallback K-means pass over shipment candidates |
| `scoreShipment` | `app/lib/optimizer.ts` | `optimizeCorridor` | Browser fallback scoring with route, revenue, cargo, contract, schedule, and cluster signals |
| `optimizeCorridor` | `app/lib/optimizer.ts` | `Home` through `useMemo` | Browser fallback optimiser only, used if the backend is unavailable |
| `routeNodesFor` | `app/lib/optimizer.ts` | `buildRecommendedActions` | Builds browser fallback route sequences from corridor and shipment fields |
| `instructionFor` | `app/lib/optimizer.ts` | `buildRecommendedActions` | Converts mode and detour policy into a simple operating instruction |
| `buildRecommendedActions` | `app/lib/optimizer.ts` | `optimizeCorridor` | Creates browser fallback action cards when the backend is unavailable |
| `formatCurrency` | `app/lib/formatters.ts` | Metric and row render logic | Formats rupee values in Indian currency style |
| `formatShortCurrency` | `app/lib/formatters.ts` | Metric cards | Shortens currency into lakh and crore labels |
| `Metric` | `app/components/Metric.tsx` | `Home` | Reusable KPI card component |
| `corridors`, `retailProfiles` | `app/data/fallback-data.ts` | `Home` | Local fallback data used when the backend is unavailable |

### Backend Functions

| Function Or Object | File | Called By | Purpose |
| --- | --- | --- | --- |
| `read_csv_table` | `backend/repository.py` | `load_dataset` | Reads a CSV table from `backend/data` |
| `load_dataset` | `backend/repository.py` | Repository startup and tests | Loads all CSV tables and converts them into API-ready objects |
| `run_kmeans` | `backend/clustering.py` | `build_shipment_cluster_lookup` | Runs deterministic K-means on standardised shipment feature vectors |
| `cluster_fit_score` | `backend/clustering.py` | `build_shipment_cluster_lookup` | Converts a shipment-cluster centroid into a scoring signal |
| `build_shipment_cluster_lookup` | `backend/clustering.py` | `POST /api/optimise` | Assigns each shipment to a K-means group and returns cluster fit, label, adjustment, and insight |
| `score_shipment` | `backend/optimizer.py` | `optimise_corridor` | Scores shipment candidates using rule-based factors plus K-means cluster adjustment |
| `route_nodes_for` | `backend/optimizer.py` | `build_recommended_actions` | Builds the recommended route sequence from shipment origin, corridor waypoints, and shipment destination |
| `instruction_for` | `backend/optimizer.py` | `build_recommended_actions` | Creates mode-specific operating instructions for road, air, sea, and staging cargo |
| `build_recommended_actions` | `backend/optimizer.py` | `optimise_corridor` | Converts accepted shipment matches into business-readable action recommendations |
| `build_operational_summary` | `backend/optimizer.py` | `optimise_corridor` | Summarises driver quality, contracts, compatibility, clearance, cost, and K-means fit |
| `optimise_corridor` | `backend/optimizer.py` | `POST /api/optimise` | Accepts, declines, and measures candidate shipments for one corridor |
| `dataset_summary` | `backend/repository.py` | `/api/health` and `/api/tables` | Returns table counts and total scanned capacity |
| `find_corridor` | `backend/repository.py` | Corridor endpoints and optimiser endpoint | Looks up a corridor by ID |
| `CapacityIQHandler.do_GET` | `backend/server.py` | HTTP server | Routes read-only API requests |
| `CapacityIQHandler.do_POST` | `backend/server.py` | HTTP server | Routes optimiser requests |
| `run` | `backend/server.py` | CLI entrypoint | Starts the local backend service |

### Data Generation Functions

| Function | File | Purpose |
| --- | --- | --- |
| `make_capacity_rows` | `scripts/seed_dummy_data.py` | Creates road, air, sea, and staging capacity for every corridor |
| `make_shipments` | `scripts/seed_dummy_data.py` | Creates 2,400 realistic candidate shipment rows |
| `make_hubs` | `scripts/seed_dummy_data.py` | Creates staging and consolidation hub rows |
| `make_partners` | `scripts/seed_dummy_data.py` | Creates transporter, warehouse, shipping, and air cargo partners |
| `make_retail_rows` | `scripts/seed_dummy_data.py` | Creates retail route profiles and assortment tables |

## User Action Mapping

| User Action | Frontend State Or Function | Result |
| --- | --- | --- |
| Select a freight corridor | `setSelectedCorridorId` | Updates the draft corridor input |
| Toggle Britannia anchor | `setAnchorEnabled` | Updates the draft anchor setting |
| Move Anchor volume | `setAnchorMultiplier` | Updates the draft anchor tonnes assumption |
| Move Max detour | `setMaxDetour` | Updates the draft route flexibility policy |
| Move Compatibility guardrail | `setGuardrail` | Updates the draft compatibility threshold |
| Move Driver score floor | `setMinDriverScore` | Rejects operators below the selected quality floor |
| Move Air clearance cap | `setMaxClearanceMinutes` | Rejects air cargo whose handling, security, customs, and layover time exceeds the cap |
| Toggle Prefer contracted capacity | `setPreferContracted` | Penalises spot-market capacity when the optimiser scores loads |
| Select Run optimiser | `setAppliedNetworkInputs` | Applies the visible draft inputs and requests backend optimisation |
| Switch to Airport retail | `setView` | Shows the retail optimisation workspace |
| Select a passenger route | `setSelectedRetailId` | Changes product allocation and passenger profile |
| Move Passenger signal | `setPassengerWave` | Changes sales uplift and optimised revenue estimate |

## Production Extension

The current backend is intentionally simple and local. A production version should add:

| Layer | Suggested Direction |
| --- | --- |
| Database | PostgreSQL or another relational database for shipments, capacity, rates, partners, users, and approvals |
| Backend API | FastAPI or Node.js service with authentication, saved scenarios, booking, pricing, and audit history |
| Optimisation Engine | Python service using OR Tools, Pyomo, or custom solvers for vehicle routing, backhaul matching, multimodal routing, and time windows |
| Forecasting | Demand, capacity, passenger, and disruption forecasting models |
| Integrations | ERP, TMS, WMS, transporter GPS, airline cargo, port systems, POS, and flight schedule APIs |
| Governance | Compatibility rules, food safety, pharma handling, customer approvals, and compliance workflows |

## Verification

The current repository has been checked with:

```bash
npm run test:backend
npm run lint
npm run build
curl http://127.0.0.1:8000/api/tables
curl -I http://localhost:3000/
```

Expected result:

| Check | Expected Outcome |
| --- | --- |
| Backend tests | All tests pass |
| Lint | No lint errors |
| Build | Frontend build completes |
| API tables | JSON table counts are returned |
| Frontend page | HTTP `200 OK` |

## Demo Study Documents

The `docs` folder includes preparation documents:

| Document | Purpose |
| --- | --- |
| `docs/CapacityIQ_Study_Guide_FAQ.docx` | One-hour meeting study guide with demo agenda, feature explanation, AI engine explanation, FAQs, and closing talk track |
| `docs/CapacityIQ_Demo_Runbook.docx` | Practical demo walkthrough for operating the local app during a live session |
