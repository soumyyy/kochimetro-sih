# Kochi Metro Induction & IBL Planner

## One-liner
Nightly decision-support for 25 trainsets that delivers a "tomorrow" plan: 7–9 Active, the rest Standby or IBL; schedules IBL jobs (21:00–05:30), assigns depot stabling & turnout order, and optimizes safety, service readiness, branding exposure, mileage balancing, and operations (shunting/turnout time).

## Scope & Non-Goals

### In Scope (MVP, offline)
- Single depot (Muttom)
- Static GTFS-derived demand
- CSV/JSON ingest for fitness/Maximo
- Full plan with explanations
- What-if analysis

### Not in Scope (MVP)
- Production integrations
- Real-time mid-day rescheduling
- Multi-depot support
- Crew rostering (beyond cleaning skills)

## System Overview

### Service Envelope & Assumptions
- **Fleet**: N=25 four-car trainsets
- **Service window**: 06:00–22:30 IST (constant H_active = 16.5 h)
- **Active band**: Active_min=7, Active_max=9
- **Night work window**: 21:00–05:30
- **Day types**: WK (Mon–Sat), WE (Sun)
- **Timezone**: Asia/Kolkata

## Architecture

### Data Model
The system uses a comprehensive PostgreSQL database with the following key tables:

- `trains` - Fleet roster and status
- `fitness_certificates` - Safety certifications by department
- `job_cards` - Maintenance work orders from Maximo
- `sponsors`, `branding_campaigns` - Advertising contracts and commitments
- `train_wraps` - Active branding assignments
- `service_log` - Historical service records
- `branding_exposure_log` - Derived branding performance
- `mileage_log` - Cumulative mileage tracking
- `depots`, `stabling_bays` - Depot infrastructure
- `bay_conflicts`, `depot_routes` - Operational constraints
- `bay_occupancy` - IBL scheduling results
- `induction_plans` - Daily plan headers
- `induction_plan_items` - Per-train decisions and explanations
- `turnout_plan` - Morning turnout sequencing
- `alerts`, `overrides` - Exception handling

### Optimization Engine
Three-stage nightly optimization (21:00–23:00) using CP-SAT (OR-Tools) or MILP:

#### Stage 1: Assignment (Active / Standby / IBL)
- **Objective**: Minimize risk, branding deficit, mileage variance, cleaning penalties, shunting costs
- **Constraints**: Active count limits, fitness gates, work order blocks
- **Decision Variables**: xA_i, xS_i, xM_i (Active/Standby/IBL assignment)

#### Stage 2: IBL Scheduler (RCPSP / Job-shop)
- **Objective**: Complete all IBL jobs by 05:30, minimize moves
- **Constraints**: Bay capacity, crew skills, job durations
- **Decision Variables**: y_{i,b,t} (bay occupancy), finish times

#### Stage 3: Depot Stabling & Morning Turnout
- **Stage 3A**: Slot assignment minimizing exit times
- **Stage 3B**: Turnout sequencing minimizing conflicts and setup times

### Technology Stack
- **Backend**: Python, FastAPI, SQLAlchemy, OR-Tools, PostgreSQL
- **Frontend**: React, Vite, Tailwind CSS, shadcn/ui
- **Optimization**: Google OR-Tools (CP-SAT solver)
- **Database**: PostgreSQL with advanced constraints

## Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Git

### Environment Variables
```bash
# Backend
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/metro
APP_TIMEZONE=Asia/Kolkata
CORS_ORIGINS=http://localhost:5173

# Frontend
VITE_API_BASE_URL=http://localhost:8000
```

### Quick Start

1. **Clone and setup:**
```bash
git clone <repository-url>
cd kochimetro-sih
```

2. **Database setup:**
```bash
# Create PostgreSQL database
createdb metro

# Run schema (includes seed data)
psql -d metro -f db.sql
```

3. **Backend setup:**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

4. **Frontend setup:**
```bash
cd frontend
npm install
npm run dev
```

## API Reference

### Data Ingestion
- `POST /ingest/gtfs` - Update GTFS-derived service expectations
- `POST /ingest/fitness` - Import fitness certificates (CSV/JSON)
- `POST /ingest/maximo` - Import work orders (CSV/JSON)

### Planning Operations
- `POST /plans` - Create new plan
- `POST /plans/{plan_id}/run` - Execute 3-stage optimization
- `PATCH /plans/{plan_id}/items/{train_id}` - Manual overrides
- `POST /plans/{plan_id}/finalize` - Lock plan

### Analytics & Reporting
- `GET /plans/{plan_id}/explain/{train_id}` - Decision explanations
- `POST /plans/{plan_id}/whatif` - Scenario analysis
- `GET /branding/rollup` - Exposure analytics
- `GET /mileage/variance` - Fleet mileage analysis

## Frontend Views

### PlanBoard (Main Dashboard)
- 3-column layout: Active / Standby / IBL
- Drag-and-drop train management
- Real-time KPI display
- Manual override capabilities

### IBL Gantt
- Per-bay timeline visualization
- Crew capacity overlays
- Conflict highlighting

### DepotView
- Stabling bay assignments
- Turnout sequencing with ETAs
- Conflict warnings

### SponsorDash
- Branding exposure analytics
- Deficit tracking
- Contract compliance

## Optimization Details

### Objective Function (Lexicographic)
1. **Stage 1**: Reliability and safety dominate
2. **Stage 2**: Complete IBL by 05:30
3. **Stage 3**: Minimize exit times and conflicts

### Key Constraints
- Active count: 7 ≤ ΣxA_i ≤ 9
- Fitness gates: xA_i ≤ fit_ok_i
- Work order blocks: xA_i ≤ (1 - wo_blocking_i)
- Branding deficits: sBrand_i ≥ brand_target - H_active * xA_i
- Mileage balancing: |km_cum_i + expected_km_i * xA_i - target_avg|

### Default Weights
```python
w_risk = 1.0      # Safety and reliability
w_brand = 0.6     # Branding commitments
w_mileage = 0.2   # Fleet balancing
w_clean = 0.4     # Maintenance scheduling
w_shunt = 0.15    # Operational efficiency
w_override = 3.0  # Manual override penalty
```

## Development Workflow

### Daily Development Cycle
1. **Feature extraction** (deterministic pre-compute)
2. **Stage 1 optimization** (Assignment)
3. **Stage 2 optimization** (IBL scheduling)
4. **Stage 3 optimization** (Stabling & turnout)
5. **Plan persistence** and explanation generation

### Testing Strategy
- Unit tests for constraint satisfaction
- Property tests for optimization invariants
- Integration tests for end-to-end workflows
- Performance validation (stages complete within time windows)

## Performance Requirements
- Stage 1: ≤ few seconds for 25 trains
- Stage 2: Complete IBL scheduling within time windows
- Stage 3: Optimal assignment and sequencing
- Total nightly run: < 2 hours (21:00-23:00 window)

## Data Sources & Integration

### GTFS Integration
- Static schedules for expected_km_if_active_i
- Route and timing data for service planning

### Fitness Certificates
- Department-wise validity tracking
- Safety gate enforcement

### Maximo Work Orders
- Job cards with priority and safety criticality
- IBL requirement determination

### Branding Systems
- Sponsor contracts and exposure commitments
- Rolling window deficit calculations

## Security Considerations
- Plan finalization workflow
- Audit trails for overrides
- Data validation and integrity constraints

## Monitoring & Observability
- Optimization solver performance metrics
- Constraint violation tracking
- Plan quality KPIs and trends

## Future Enhancements (Post-MVP)
- Live Maximo API integration
- Real-time rescheduling capabilities
- Multi-depot support
- Advanced risk modeling
- Energy-aware optimization
- Crew rostering integration

## Mathematical Specification

### Stage 1: Assignment Problem
```
min Σ_i [w_risk * Risk_i * xA_i + w_brand * sBrand_i + w_mileage * (sMilePos_i + sMileNeg_i) + w_clean * needs_clean_i * (1 - xM_i) + w_shunt * exit_time_cost_hint_i * xA_i + w_override * ovr_i]

s.t. ∀i: xA_i + xS_i + xM_i = 1
     Active_min ≤ Σ_i xA_i ≤ Active_max
     ∀i: xA_i ≤ fit_ok_i + ovr_i
     ∀i: xA_i ≤ (1 - wo_blocking_i) + ovr_i
     ∀i: sBrand_i ≥ brand_target_h_i - H_active * xA_i
     ∀i: sMilePos_i - sMileNeg_i = (km_cum_i + expected_km_if_active_i * xA_i) - km_target_avg
```

### Stage 2: IBL Scheduling
```
min Σ_i u_i + ε Σ_{i,b,t} MoveCost_{i,b,t} y_{i,b,t}

s.t. ∀b,t: Σ_i y_{i,b,t} ≤ cap_bay_{b,t}
     ∀t,s: Σ_i skill_need_{i,s} y_{i,*,t} ≤ cap_crew_{s,t}
     ∀i: Σ_{b,t} y_{i,b,t} Δt ≥ clean_duration_i xM_i
```

### Stage 3: Stabling & Turnout
```
min Σ_i Σ_p ExitTime_{i,p} z_{i,p} + Σ_{i≠j} S_{i→j} δ_{i,j}

s.t. ∀i: Σ_p z_{i,p} = 1
     ∀p: Σ_i z_{i,p} ≤ 1
     ∀i≠j: δ_{i,j} + δ_{j,i} = 1
     ∀i≠j: start_j ≥ start_i + Proc_i + S_{i→j} - M(1-δ_{i,j})
```

## Contributing
1. Follow the established optimization framework
2. Maintain mathematical rigor in constraint modeling
3. Ensure UI/UX consistency with existing patterns
4. Add comprehensive tests for new features
5. Update documentation for API changes

## Support
For questions about the optimization model, mathematical constraints, or system architecture, refer to the comments in the source code or contact the development team.

---

**Note**: This system optimizes complex operational constraints while maintaining mathematical rigor and operational feasibility. The three-stage approach ensures that safety and reliability considerations dominate, followed by scheduling efficiency and operational optimization.
