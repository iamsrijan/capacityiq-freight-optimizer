# CapacityIQ Freight And Capacity Optimiser

CapacityIQ is a local full-stack prototype for an AI-powered freight and capacity optimisation marketplace. It demonstrates how shippers, transporters, air cargo capacity, sea freight capacity, and staging hubs can be matched so existing assets work harder before new assets are purchased.

The freight example uses Britannia as the anchor demand partner. Britannia creates predictable base movement into a corridor. The platform then looks for compatible third-party cargo that can use empty or underused return capacity. The same optimisation idea is also shown for airport retail, where passenger and route signals change product allocation inside existing shop space.

## What The Application Does

The application has two workspaces.

| Workspace | Purpose | Main Output |
| --- | --- | --- |
| Freight Optimisation | Match cargo demand with unused road, air, sea, and staging capacity | Empty kilometres avoided, matched cargo, unlocked revenue, load factor, and guardrail queue |
| Airport Retail Optimisation | Match product mix with passenger route demand | Product allocation, uplift estimate, optimised revenue, and store productivity message |

The core thesis is simple:

> Do not buy more assets first. Use existing assets more intelligently.

## Screenshots

### Freight Workspace

![Freight workspace](docs/screenshots/freight-workspace-annotated.jpg)

| Marker | Area | What It Does |
| --- | --- | --- |
| 1 | Workspace tabs | Switch between Freight and Airport retail views |
| 2 | Network inputs | Choose corridor, anchor demand, detour policy, and guardrail strictness |
| 3 | Key result cards | Show empty kilometres avoided, matched cargo, revenue, and unit cost impact |
| 4 | Live corridor map | Show the selected corridor and multimodal movement pattern |
| 5 | Capacity and economics rail | Show mode utilisation, savings, capacity, and review queue |

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
| 1 | Route clusters | Selects the passenger route group |
| 2 | Passenger signal slider | Models stronger or weaker demand |
| 3 | Product allocation board | Shows how store space should be assigned |
| 4 | Sales uplift | Shows expected uplift from better assortment matching |
| 5 | Retail metrics | Shows flights, revenue, and asset productivity |

## Local Setup

Clone the project into any folder on your machine or server:

```bash
git clone https://github.com/iamsrijan/capacityiq-freight-optimizer.git
cd capacityiq-freight-optimizer
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

### Why The Browser URL Stays On Port 3000

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

You can also verify this in the browser developer tools under the Network tab, or by opening the backend health endpoint directly:

```bash
http://127.0.0.1:8000/api/health
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
| `retail_profiles.csv` | 8 | Airport route clusters and revenue assumptions |
| `retail_assortments.csv` | 40 | Product allocation and uplift assumptions by route cluster |

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
    "guardrail": 74
  }'
```

### Optimiser Response Shape

The optimiser returns:

| Field | Meaning |
| --- | --- |
| `accepted` | Shipments accepted into capacity |
| `declined` | Shipments rejected or queued for review |
| `remaining` | Remaining tonnes by mode |
| `modeUtilisation` | Used, remaining, and utilisation by mode |
| `bookableTonnes` | Tonnes the optimiser is allowed to allocate after operating reserve |
| `reserveTonnes` | Capacity held back for service reliability, slot risk, and operational buffer |
| `matchedTonnes` | Total tonnes matched |
| `revenue` | Estimated revenue unlocked |
| `emptyKmAvoided` | Empty kilometres avoided |
| `costSaved` | Operating cost avoided |
| `loadFactor` | Return capacity load factor |
| `unitCostDrop` | Estimated freight unit cost reduction |
| `anchorTonnes` | Anchor demand volume used in the optimiser run |

## Frontend Data Flow

The frontend starts with embedded sample data so the app can still open if the backend is not running. When the backend is available, the app fetches:

1. `/api/corridors`
2. `/api/retail-profiles`
3. `/api/health`

After loading succeeds, the top status bar shows the CSV shipment count. Freight controls act as draft network inputs. When the user selects Run optimiser, the frontend posts the visible corridor, anchor, detour, and guardrail settings to `/api/optimise`. The backend returns the displayed accepted matches, rejected queue, mode utilisation, revenue, empty kilometres avoided, cost saved, load factor, and unit cost impact.

If backend loading or backend optimisation fails, the app displays fallback status text and continues to work with the smaller embedded browser-side model.

Capacity Inventory bars show matched tonnes against operationally available capacity. The backend also keeps mode-specific reserves, so road, air, sea, and staging do not automatically show 100% utilisation just because demand exists.

## Project Architecture

```text
capacityiq-freight-optimizer/
  app/
    page.tsx              Frontend screen, UI state, API loading, fallback data
    layout.tsx            Root app shell and metadata
    globals.css           Dashboard styling and responsive layout
  backend/
    server.py             Local Python API and optimiser
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
| `useEffect(loadBackendData)` | `app/page.tsx` | `Home` | Fetches CSV-backed corridors, retail profiles, and dataset counts from the backend |
| `useEffect(loadBackendOptimization)` | `app/page.tsx` | `Home` | Posts the applied freight inputs to `/api/optimise` and stores backend-calculated results |
| `scoreShipment` | `app/page.tsx` | `optimizeCorridor` | Browser fallback scoring only, used if the backend is unavailable |
| `optimizeCorridor` | `app/page.tsx` | `Home` through `useMemo` | Browser fallback optimiser only, used if the backend is unavailable |
| `formatCurrency` | `app/page.tsx` | Metric and row render logic | Formats rupee values in Indian currency style |
| `formatShortCurrency` | `app/page.tsx` | Metric cards | Shortens currency into lakh and crore labels |
| `Metric` | `app/page.tsx` | `Home` | Reusable KPI card component |

### Backend Functions

| Function Or Object | File | Called By | Purpose |
| --- | --- | --- | --- |
| `read_csv_table` | `backend/server.py` | `load_dataset` | Reads a CSV table from `backend/data` |
| `load_dataset` | `backend/server.py` | Server startup and tests | Loads all CSV tables and converts them into API-ready objects |
| `score_shipment` | `backend/server.py` | `optimise_corridor` | Scores shipment candidates using the backend version of the scoring logic |
| `optimise_corridor` | `backend/server.py` | `POST /api/optimise` | Accepts, declines, and measures candidate shipments for one corridor |
| `dataset_summary` | `backend/server.py` | `/api/health` and `/api/tables` | Returns table counts and total scanned capacity |
| `find_corridor` | `backend/server.py` | Corridor endpoints and optimiser endpoint | Looks up a corridor by ID |
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
| Select Run optimiser | `setAppliedNetworkInputs` | Applies the visible draft inputs and requests backend optimisation |
| Switch to Airport retail | `setView` | Shows the retail optimisation workspace |
| Select a retail route cluster | `setSelectedRetailId` | Changes product allocation and passenger profile |
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
