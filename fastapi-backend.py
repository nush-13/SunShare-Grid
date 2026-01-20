"""
Phase 3: FastAPI Backend for Solar Microgrid Optimizer
Implements core optimization engine with geospatial analysis
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import numpy as np
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Solar Microgrid Optimizer API",
    description="Climate & Geospatial Data-Driven Energy Distribution",
    version="0.3.0"
)

# CORS configuration for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# DATA MODELS
# ============================================================================

class Building(BaseModel):
    """Building data structure"""
    id: str
    x: float
    y: float
    name: str
    solar: float  # 0-100 (solar potential %)
    demand: float  # kWh/day
    income: str  # 'low', 'medium', 'high'
    type: str  # 'residential', 'commercial', 'mixed', 'public'

class SolarAnalysisRequest(BaseModel):
    """Request for solar suitability analysis"""
    buildings: List[Building]
    area: str
    season: Optional[str] = "winter"

class DemandEstimationRequest(BaseModel):
    """Request for demand estimation"""
    buildings: List[Building]
    area: str

class OptimizationRequest(BaseModel):
    """Request for optimization engine"""
    buildings: List[Building]
    solar_weight: float  # 0-1
    equity_weight: float  # 0-1
    target_stations: int
    sharing_radius: float  # km

class OptimizationResponse(BaseModel):
    """Response from optimization engine"""
    status: str
    selected_stations: List[str]
    total_capacity: float
    coverage: float
    equity_score: float
    station_details: List[Dict]
    impact_metrics: Dict

# ============================================================================
# PHASE 3A: SOLAR SUITABILITY ANALYSIS ENGINE
# ============================================================================

class SolarAnalysisEngine:
    """
    Analyzes satellite solar irradiance data and calculates per-building potential
    Layer 2: Intelligence Layer - Solar Suitability Scoring
    """
    
    # NREL Delhi-NCR baseline irradiance data (kWh/m²/day)
    IRRADIANCE_BASELINE = {
        'sample-delhi': 5.4,
        'north-delhi': 5.2,
        'south-delhi': 5.6,
        'dwarka': 5.5
    }
    
    # Seasonal adjustments
    SEASONAL_MULTIPLIER = {
        'winter': 1.0,  # Jan-Mar: clearest skies
        'summer': 0.95,  # Apr-Jun: haze/pollution
        'monsoon': 0.7,  # Jul-Sep: clouds
        'post-monsoon': 0.85  # Oct-Dec
    }
    
    # Shading proxy: tall buildings reduce nearby solar by distance factor
    SHADING_PENALTY_RADIUS = 0.3  # km
    
    @staticmethod
    def calculate_solar_score(building: Building, all_buildings: List[Building], area: str, season: str) -> Dict:
        """
        Calculate solar suitability for a single building
        
        Returns:
            - solar_score (0-100): Composite score
            - irradiance (kWh/m²/day): Adjusted irradiance
            - shading_factor (0-1): Effect of nearby buildings
            - efficiency (0-1): Expected panel efficiency at this location
        """
        base_irradiance = SolarAnalysisEngine.IRRADIANCE_BASELINE.get(area, 5.4)
        seasonal_factor = SolarAnalysisEngine.SEASONAL_MULTIPLIER.get(season, 1.0)
        adjusted_irradiance = base_irradiance * seasonal_factor
        
        # Building's intrinsic solar potential (from input data)
        intrinsic_solar = building.solar / 100.0
        
        # Shading penalty from nearby buildings
        shading_factor = 1.0
        for other in all_buildings:
            if other.id != building.id:
                # Calculate distance in km (normalized x,y coords)
                dist = np.sqrt((building.x - other.x)**2 + (building.y - other.y)**2) / 100.0
                if dist < SolarAnalysisEngine.SHADING_PENALTY_RADIUS:
                    # Closer buildings cause more shading
                    penalty = (1 - dist / SolarAnalysisEngine.SHADING_PENALTY_RADIUS) * 0.1
                    shading_factor -= penalty
        
        shading_factor = max(0.6, min(1.0, shading_factor))  # Clamp 0.6-1.0
        
        # Panel efficiency (modern panels: 18-22%)
        efficiency = 0.18 + (intrinsic_solar * 0.04)
        
        # Composite solar score
        solar_score = (intrinsic_solar * 0.5 + shading_factor * 0.3 + efficiency * 0.2) * 100
        
        return {
            'building_id': building.id,
            'solar_score': round(solar_score, 1),
            'irradiance': round(adjusted_irradiance, 2),
            'shading_factor': round(shading_factor, 2),
            'efficiency': round(efficiency, 2),
            'estimated_capacity_kw': round(building.solar * efficiency, 2)
        }

# ============================================================================
# PHASE 3B: DEMAND ESTIMATION ENGINE
# ============================================================================

class DemandEstimationEngine:
    """
    Estimates building-level electricity consumption from proxies
    Layer 2: Intelligence Layer - Demand Estimation Model
    """
    
    # Default consumption profiles (kWh/day)
    CONSUMPTION_BY_TYPE = {
        'residential': {'base': 1.5, 'per_unit': 0.5},
        'commercial': {'base': 8.0, 'per_unit': 2.0},
        'mixed': {'base': 5.0, 'per_unit': 1.2},
        'public': {'base': 6.0, 'per_unit': 1.5}  # schools, hospitals, govt
    }
    
    # Income-based multiplier (low-income may have lower access = lower reported demand)
    INCOME_MULTIPLIER = {
        'low': 0.8,
        'medium': 1.0,
        'high': 1.3
    }
    
    # Peak demand factor (peak / average)
    PEAK_FACTOR = 1.5
    
    @staticmethod
    def estimate_demand(building: Building, all_buildings: List[Building]) -> Dict:
        """
        Estimate daily electricity demand for a building
        
        Returns:
            - daily_demand (kWh): Average daily consumption
            - peak_demand (kWh): Peak hour demand
            - priority_score (0-1): Equity priority (low-income = higher)
        """
        building_type = building.type
        income = building.income
        
        # Base consumption from building type
        profile = DemandEstimationEngine.CONSUMPTION_BY_TYPE.get(building_type, {'base': 5.0, 'per_unit': 1.0})
        base_demand = profile['base'] + profile['per_unit'] * (building.demand / 10.0)
        
        # Income adjustment
        income_mult = DemandEstimationEngine.INCOME_MULTIPLIER.get(income, 1.0)
        adjusted_demand = base_demand * income_mult
        
        # Peak demand (typically 1.5x average)
        peak_demand = adjusted_demand * DemandEstimationEngine.PEAK_FACTOR
        
        # Priority score for equity (low-income = higher priority)
        priority_score = {'low': 0.9, 'medium': 0.5, 'high': 0.3}.get(income, 0.5)
        
        return {
            'building_id': building.id,
            'daily_demand': round(adjusted_demand, 2),
            'peak_demand': round(peak_demand, 2),
            'base_type': building_type,
            'priority_score': round(priority_score, 2)
        }

# ============================================================================
# PHASE 3C: OPTIMIZATION ENGINE (CORE ALGORITHM)
# ============================================================================

class OptimizationEngine:
    """
    Selects optimal rooftops for solar stations and calculates coverage
    Layer 2: Intelligence Layer - Optimization Engine
    
    Algorithm: Weighted scoring with geospatial clustering
    1. Score each building: (solar_score × solar_weight) + (equity_factor × equity_weight)
    2. Sort by composite score
    3. Select top N as solar stations
    4. Calculate coverage radius and grid connections
    5. Compute impact metrics
    """
    
    @staticmethod
    def optimize_placement(
        buildings: List[Building],
        solar_engine: SolarAnalysisEngine,
        demand_engine: DemandEstimationEngine,
        solar_weight: float,
        equity_weight: float,
        target_stations: int,
        sharing_radius: float,
        season: str = 'winter',
        area: str = 'sample-delhi'
    ) -> OptimizationResponse:
        """
        Core optimization algorithm
        
        Args:
            buildings: List of building objects
            solar_engine: Solar analysis engine instance
            demand_engine: Demand estimation engine instance
            solar_weight: Weight for solar potential (0-1)
            equity_weight: Weight for equity (0-1)
            target_stations: Target number of solar stations
            sharing_radius: Energy sharing radius in km
            season: Current season
            area: Geographic area
        
        Returns:
            OptimizationResponse with selected stations and metrics
        """
        
        # Step 1: Calculate solar scores for all buildings
        solar_scores = [
            solar_engine.calculate_solar_score(b, buildings, area, season)
            for b in buildings
        ]
        
        # Step 2: Calculate demand estimates
        demand_scores = [
            demand_engine.estimate_demand(b, buildings)
            for b in buildings
        ]
        
        # Step 3: Composite scoring and ranking
        scored_buildings = []
        for building in buildings:
            solar_data = next(s for s in solar_scores if s['building_id'] == building.id)
            demand_data = next(d for d in demand_scores if d['building_id'] == building.id)
            
            # Normalize scores to 0-1
            normalized_solar = solar_data['solar_score'] / 100.0
            normalized_equity = demand_data['priority_score']  # Already 0-1
            
            # Weighted composite score
            composite_score = (
                normalized_solar * solar_weight +
                normalized_equity * equity_weight
            )
            
            # Additional factor: solar vs demand ratio (prefer high solar, low demand)
            solar_demand_ratio = building.solar / max(building.demand, 1)
            composite_score += (solar_demand_ratio / 10.0) * 0.2  # 20% weight for ratio
            
            scored_buildings.append({
                'building': building,
                'composite_score': composite_score,
                'solar_data': solar_data,
                'demand_data': demand_data
            })
        
        # Step 4: Select top N stations
        scored_buildings.sort(key=lambda x: x['composite_score'], reverse=True)
        selected_stations = scored_buildings[:min(target_stations, len(scored_buildings))]
        
        # Step 5: Calculate coverage and connections
        station_ids = [s['building'].id for s in selected_stations]
        total_capacity = sum(s['solar_data']['estimated_capacity_kw'] for s in selected_stations)
        total_demand = sum(b.demand for b in buildings)
        coverage = min(100, (total_capacity / max(total_demand, 1)) * 100)
        
        # Equity score: % of low-income buildings served
        low_income_served = sum(1 for s in selected_stations if s['building'].income == 'low')
        equity_score = (low_income_served / max(len(selected_stations), 1)) * 100
        
        # Step 6: Build detailed station information
        station_details = []
        for station in selected_stations:
            # Find buildings within sharing radius
            connected_buildings = []
            for building in buildings:
                if building.id != station['building'].id:
                    dist_km = np.sqrt(
                        (station['building'].x - building.x)**2 + 
                        (station['building'].y - building.y)**2
                    ) / 100.0 * 15  # Scale factor to real km
                    
                    if dist_km <= sharing_radius:
                        connected_buildings.append({
                            'id': building.id,
                            'distance_km': round(dist_km, 2),
                            'demand_kWh': building.demand,
                            'income': building.income
                        })
            
            station_details.append({
                'id': station['building'].id,
                'name': station['building'].name,
                'capacity_kw': station['solar_data']['estimated_capacity_kw'],
                'solar_score': station['solar_data']['solar_score'],
                'irradiance': station['solar_data']['irradiance'],
                'efficiency': station['solar_data']['efficiency'],
                'connected_buildings': connected_buildings,
                'coverage_count': len(connected_buildings)
            })
        
        # Step 7: Impact metrics
        co2_offset_per_kwh = 0.62  # kg CO2 per kWh vs grid
        annual_co2_avoided = (total_capacity * 365 * co2_offset_per_kwh) / 1000  # metric tons
        
        peak_reduction = (total_capacity / max(total_demand, 1)) * 100
        diesel_generators_replaced = int(np.ceil(total_capacity / 50))  # 50 kW per generator
        
        # Beneficiaries: low-income residents in served buildings
        low_income_count = sum(1 for b in buildings if b.income == 'low')
        beneficiaries = low_income_count * 200  # Average residents per building
        
        impact_metrics = {
            'co2_avoided_metric_tons': round(annual_co2_avoided, 1),
            'peak_load_reduction_percent': round(peak_reduction, 1),
            'diesel_generators_replaced': diesel_generators_replaced,
            'low_income_beneficiaries': beneficiaries,
            'total_capacity_kw': round(total_capacity, 1),
            'avg_solar_efficiency': round(
                sum(s['solar_data']['efficiency'] for s in selected_stations) / len(selected_stations), 3
            )
        }
        
        return OptimizationResponse(
            status='success',
            selected_stations=station_ids,
            total_capacity=round(total_capacity, 1),
            coverage=round(coverage, 1),
            equity_score=round(equity_score, 1),
            station_details=station_details,
            impact_metrics=impact_metrics
        )

# ============================================================================
# API ENDPOINTS
# ============================================================================

# Engine instances (singleton pattern)
solar_engine = SolarAnalysisEngine()
demand_engine = DemandEstimationEngine()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Solar Microgrid Optimizer API",
        "version": "0.3.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/analyze-solar")
async def analyze_solar(request: SolarAnalysisRequest):
    """
    Analyze solar suitability for all buildings
    
    Returns solar scores, irradiance, shading factors, and estimated capacity
    """
    try:
        logger.info(f"Analyzing solar for {len(request.buildings)} buildings in {request.area}")
        
        results = [
            solar_engine.calculate_solar_score(
                building, request.buildings, request.area, request.season
            )
            for building in request.buildings
        ]
        
        avg_irradiance = np.mean([r['irradiance'] for r in results])
        high_potential = sum(1 for r in results if r['solar_score'] > 60)
        
        return {
            "status": "success",
            "area": request.area,
            "season": request.season,
            "avg_irradiance": round(avg_irradiance, 2),
            "high_potential_count": high_potential,
            "total_buildings": len(request.buildings),
            "results": results
        }
    except Exception as e:
        logger.error(f"Solar analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/estimate-demand")
async def estimate_demand(request: DemandEstimationRequest):
    """
    Estimate electricity demand for all buildings
    
    Returns demand estimates, peak factors, and priority scores
    """
    try:
        logger.info(f"Estimating demand for {len(request.buildings)} buildings in {request.area}")
        
        results = [
            demand_engine.estimate_demand(building, request.buildings)
            for building in request.buildings
        ]
        
        total_demand = sum(r['daily_demand'] for r in results)
        priority_areas = sum(1 for r in results if r['priority_score'] > 0.7)
        
        return {
            "status": "success",
            "area": request.area,
            "total_daily_demand": round(total_demand, 1),
            "priority_areas": priority_areas,
            "total_buildings": len(request.buildings),
            "results": results
        }
    except Exception as e:
        logger.error(f"Demand estimation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/optimize-placement")
async def optimize_placement(request: OptimizationRequest):
    """
    Core optimization engine: Select optimal solar stations
    
    Returns selected stations, coverage %, equity score, and impact metrics
    """
    try:
        logger.info(f"Optimizing placement for {len(request.buildings)} buildings")
        logger.info(f"Weights - Solar: {request.solar_weight}, Equity: {request.equity_weight}")
        
        result = OptimizationEngine.optimize_placement(
            buildings=request.buildings,
            solar_engine=solar_engine,
            demand_engine=demand_engine,
            solar_weight=request.solar_weight,
            equity_weight=request.equity_weight,
            target_stations=request.target_stations,
            sharing_radius=request.sharing_radius
        )
        
        return result
    except Exception as e:
        logger.error(f"Optimization error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/impact-metrics")
async def get_impact_metrics():
    """
    Pre-calculated impact metrics for Delhi-NCR region
    """
    return {
        "region": "Delhi-NCR",
        "population": 32000000,
        "current_peak_demand_mw": 8500,
        "demand_growth_annual_percent": 9,
        "avg_grid_efficiency": 0.79,
        "transmission_losses_percent": 21,
        "co2_per_kwh_grid": 0.62,
        "solar_potential_kwh_m2_day": 5.5,
        "sunny_days_annual": 320,
        "policy_targets": {
            "renewable_by_2030_percent": 25,
            "target_solar_mw": 2000
        }
    }

@app.post("/validate-data")
async def validate_data(request: OptimizationRequest):
    """
    Validate input data for consistency and completeness
    """
    try:
        issues = []
        
        # Check building counts
        if len(request.buildings) < 3:
            issues.append("Minimum 3 buildings required")
        
        # Check weight sum
        weight_sum = request.solar_weight + request.equity_weight
        if weight_sum == 0:
            issues.append("Both weights cannot be zero")
        
        # Check individual buildings
        for b in request.buildings:
            if not 0 <= b.solar <= 100:
                issues.append(f"Building {b.id}: solar must be 0-100")
            if b.demand < 0:
                issues.append(f"Building {b.id}: demand cannot be negative")
            if b.income not in ['low', 'medium', 'high']:
                issues.append(f"Building {b.id}: invalid income level")
            if b.type not in ['residential', 'commercial', 'mixed', 'public']:
                issues.append(f"Building {b.id}: invalid building type")
        
        return {
            "status": "valid" if not issues else "invalid",
            "issues": issues,
            "building_count": len(request.buildings),
            "weights_normalized": round(weight_sum, 2)
        }
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    print("""
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
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
