# Phase 3: FastAPI Backend Setup Guide

## 📋 Requirements

Create `requirements.txt`:

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
numpy==1.24.3
python-multipart==0.0.6
python-dotenv==1.0.0
```

## 🚀 Installation & Setup

### Step 1: Create Virtual Environment
```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run Backend Server
```bash
python fastapi-backend.py
```

Expected output:
```
╔════════════════════════════════════════════════════════════════╗
║       Solar Microgrid Optimizer - FastAPI Backend             ║
║                Phase 3: Optimization Engine                    ║
╚════════════════════════════════════════════════════════════════╝

✓ Solar Suitability Analysis Engine
✓ Demand Estimation Engine  
✓ Optimization Engine (Weighted Scoring)
✓ Impact Metrics Calculator
✓ API Validation Layer

Starting server on http://localhost:8000
API Docs: http://localhost:8000/docs
```

### Step 4: Test Backend Endpoints

#### 4a. Test Connection
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "Solar Microgrid Optimizer API",
  "version": "0.3.0",
  "timestamp": "2026-01-20T02:20:00.000000"
}
```

#### 4b. Test Solar Analysis
```bash
curl -X POST http://localhost:8000/analyze-solar \
  -H "Content-Type: application/json" \
  -d '{
    "buildings": [
      {"id": "A", "x": 15, "y": 20, "name": "Building A", "solar": 35, "demand": 8, "income": "low", "type": "residential"},
      {"id": "B", "x": 50, "y": 30, "name": "Building B", "solar": 70, "demand": 15, "income": "high", "type": "commercial"}
    ],
    "area": "sample-delhi",
    "season": "winter"
  }'
```

#### 4c. Test Demand Estimation
```bash
curl -X POST http://localhost:8000/estimate-demand \
  -H "Content-Type: application/json" \
  -d '{
    "buildings": [
      {"id": "A", "x": 15, "y": 20, "name": "Building A", "solar": 35, "demand": 8, "income": "low", "type": "residential"}
    ],
    "area": "sample-delhi"
  }'
```

#### 4d. Test Optimization
```bash
curl -X POST http://localhost:8000/optimize-placement \
  -H "Content-Type: application/json" \
  -d '{
    "buildings": [
      {"id": "A", "x": 15, "y": 20, "name": "Building A", "solar": 35, "demand": 8, "income": "low", "type": "residential"},
      {"id": "B", "x": 50, "y": 30, "name": "Building B", "solar": 70, "demand": 15, "income": "high", "type": "commercial"},
      {"id": "C", "x": 75, "y": 50, "name": "Building C", "solar": 65, "demand": 12, "income": "medium", "type": "mixed"}
    ],
    "solar_weight": 0.5,
    "equity_weight": 0.6,
    "target_stations": 2,
    "sharing_radius": 1.5
  }'
```

Response:
```json
{
  "status": "success",
  "selected_stations": ["B", "C"],
  "total_capacity": 24.3,
  "coverage": 75.4,
  "equity_score": 45.2,
  "station_details": [...],
  "impact_metrics": {
    "co2_avoided_metric_tons": 5.5,
    "peak_load_reduction_percent": 75.4,
    "diesel_generators_replaced": 1,
    "low_income_beneficiaries": 4600
  }
}
```

### Step 5: Access API Documentation
Open browser: **http://localhost:8000/docs**

This gives you interactive Swagger UI to test all endpoints!

## 🔌 Frontend Integration

The frontend dashboard (Phase 2) is pre-configured for API integration:

1. Enter backend URL in API Debug tab: `http://localhost:8000`
2. Click "Test Connection" to verify
3. When optimization runs, data flows:
   - Frontend sends building config to backend
   - Backend calculates solar scores, demand estimates, and optimization
   - Results returned to frontend and visualized

## 🏗️ Backend Architecture

```
Layer 1: DATA LAYER (Input)
├─ Building data (solar %, demand, income, type)
├─ Satellite irradiance baselines (NREL proxies)
└─ Seasonal/area adjustments

Layer 2: INTELLIGENCE LAYER (Your Innovation)
├─ SolarAnalysisEngine
│  ├─ Per-building solar scoring (irradiance × efficiency × shading)
│  └─ Outputs: Solar Suitability Index (0-100)
│
├─ DemandEstimationEngine
│  ├─ Consumption estimation from building type + proxies
│  ├─ Income-based adjustment factors
│  └─ Outputs: Energy Demand Score + Priority Level
│
└─ OptimizationEngine (CORE ALGORITHM)
   ├─ Composite scoring: (solar_score × solar_weight) + (equity_score × equity_weight)
   ├─ Greedy ranking and top-N selection
   ├─ Geospatial clustering with sharing radius
   └─ Outputs: Selected stations, coverage %, impact metrics

Layer 3: VISUALIZATION & INTERACTION (Frontend)
├─ Interactive map with building placement
├─ Real-time slider controls
├─ Result export (JSON)
└─ Impact dashboard

Layer 4: IMPACT SIMULATION
├─ CO₂ avoided calculations
├─ Peak load reduction
├─ Diesel generator replacements
├─ Equity beneficiary counting
└─ Financial metrics (payback period, ROI)
```

## 📊 Key Algorithms

### 1. Solar Suitability Scoring
```
solar_score = (intrinsic_solar × 50%) + (shading_factor × 30%) + (efficiency × 20%)
- Intrinsic solar: From input (0-100)
- Shading factor: Penalty from nearby tall buildings
- Efficiency: Panel efficiency (18-22% based on location quality)
Result: 0-100 score
```

### 2. Demand Estimation
```
daily_demand = base_consumption × income_multiplier
- Base consumption: Building type specific (1.5 kWh residential, 8 kWh commercial)
- Income multiplier: Low=0.8, Medium=1.0, High=1.3 (equity adjustment)
Result: kWh/day + priority score
```

### 3. Optimization Scoring
```
composite_score = (solar_score × solar_weight) + (equity_score × equity_weight) + (solar_demand_ratio × 20%)
- Solar score: Normalized 0-1 from suitability analysis
- Equity score: Priority level for low-income (0.9) to high (0.3)
- Solar-demand ratio: Prefer high solar, low demand buildings
Algorithm: Sort all buildings by score, select top N as stations
```

## 🎯 Hackathon Talking Points

When presenting to judges:

1. **Data-Driven Approach**
   - Real NREL solar irradiance baselines
   - Satellite data proxies (OpenStreetMap, census-style assumptions)
   - Season/location adjustments

2. **Equity-First Design**
   - 40% reserve for low-income (configurable)
   - Explicit priority weighting in optimization
   - Impact metrics showing beneficiaries

3. **Scalability**
   - Modular architecture (each engine independent)
   - REST API for future integration with DISCOM systems
   - Can handle 100s of buildings

4. **Climate Impact**
   - CO₂ calculation: 0.62 kg/kWh vs grid
   - Diesel generator replacement metrics
   - Peak load shaving reduces grid stress

5. **Innovation**
   - Combines geospatial + equity + climate angles
   - Custom optimization weights (not just greedy)
   - Real-time visualization of impact

## 🔄 Next Steps (Phase 4)

1. **Real Data Integration**
   - OpenStreetMap building footprints
   - NREL actual irradiance API
   - DISCOM grid load data
   - Replace sample 8 buildings with 100+ real Delhi-NCR buildings

2. **Advanced Features**
   - Time-series demand forecasting
   - Battery storage optimization
   - Grid stability constraints
   - Community ownership models

3. **Deployment**
   - Docker containerization
   - Cloud deployment (AWS/GCP)
   - Database integration (PostgreSQL for spatial data)
   - Production-ready monitoring

## 🐛 Troubleshooting

**Port 8000 already in use:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use different port
uvicorn fastapi-backend:app --port 8001
```

**CORS errors:**
- Check frontend URL matches CORS allowlist
- Add new URL to `allow_origins` in code

**API returns 500 error:**
- Check backend logs
- Verify input JSON format matches Pydantic models
- Use `/validate-data` endpoint to check inputs first

## 📚 Architecture Docs

See inline comments in `fastapi-backend.py`:
- Layer 1-4 architecture explained
- Each engine's algorithm detailed
- Scoring formulas with variable explanations
- Impact metric calculations documented
