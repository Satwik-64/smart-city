# Placeholder for dashboard_router.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import random
from datetime import datetime, timedelta
import json

router = APIRouter()

class CityKPI(BaseModel):
    name: str
    value: float
    unit: str
    trend: str
    category: str
    last_updated: str

class CityDashboard(BaseModel):
    city_name: str
    kpis: List[CityKPI]
    alerts: List[Dict[str, Any]]
    last_updated: str
    status: str

# Mock data for demonstration
CITIES_DATA = {
    "New York": {
        "air_quality": {"value": 42, "unit": "AQI", "trend": "+5%"},
        "water_usage": {"value": 1.2, "unit": "M gallons", "trend": "-3%"},
        "energy_consumption": {"value": 850, "unit": "MWh", "trend": "+2%"},
        "waste_recycled": {"value": 78, "unit": "%", "trend": "+12%"},
        "population": {"value": 8.4, "unit": "M", "trend": "+1.2%"},
        "green_spaces": {"value": 29, "unit": "%", "trend": "+3%"},
        "public_transport": {"value": 62, "unit": "%", "trend": "+5%"},
        "carbon_footprint": {"value": 4.2, "unit": "tons/person", "trend": "-8%"}
    },
    "San Francisco": {
        "air_quality": {"value": 38, "unit": "AQI", "trend": "-2%"},
        "water_usage": {"value": 0.8, "unit": "M gallons", "trend": "-5%"},
        "energy_consumption": {"value": 620, "unit": "MWh", "trend": "-3%"},
        "waste_recycled": {"value": 85, "unit": "%", "trend": "+8%"},
        "population": {"value": 0.87, "unit": "M", "trend": "+0.8%"},
        "green_spaces": {"value": 35, "unit": "%", "trend": "+5%"},
        "public_transport": {"value": 75, "unit": "%", "trend": "+7%"},
        "carbon_footprint": {"value": 3.8, "unit": "tons/person", "trend": "-12%"}
    },
    "Chicago": {
        "air_quality": {"value": 45, "unit": "AQI", "trend": "+3%"},
        "water_usage": {"value": 1.5, "unit": "M gallons", "trend": "-1%"},
        "energy_consumption": {"value": 920, "unit": "MWh", "trend": "+4%"},
        "waste_recycled": {"value": 72, "unit": "%", "trend": "+6%"},
        "population": {"value": 2.7, "unit": "M", "trend": "+0.5%"},
        "green_spaces": {"value": 26, "unit": "%", "trend": "+2%"},
        "public_transport": {"value": 58, "unit": "%", "trend": "+3%"},
        "carbon_footprint": {"value": 4.5, "unit": "tons/person", "trend": "-5%"}
    }
}

@router.get("/cities")
async def get_available_cities():
    """Get list of available cities"""
    cities = list(CITIES_DATA.keys())
    return {"cities": cities, "count": len(cities)}

@router.get("/city/{city_name}", response_model=CityDashboard)
async def get_city_dashboard(city_name: str):
    """Get dashboard data for a specific city"""
    try:
        if city_name not in CITIES_DATA:
            raise HTTPException(status_code=404, detail=f"City '{city_name}' not found")
        
        city_data = CITIES_DATA[city_name]
        
        # Convert to KPI objects
        kpis = []
        for metric_name, metric_data in city_data.items():
            kpi = CityKPI(
                name=metric_name.replace('_', ' ').title(),
                value=metric_data["value"],
                unit=metric_data["unit"],
                trend=metric_data["trend"],
                category=_get_metric_category(metric_name),
                last_updated=datetime.now().isoformat()
            )
            kpis.append(kpi)
        
        # Generate mock alerts
        alerts = _generate_city_alerts(city_name, city_data)
        
        return CityDashboard(
            city_name=city_name,
            kpis=kpis,
            alerts=alerts,
            last_updated=datetime.now().isoformat(),
            status="success"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching city dashboard: {str(e)}")

@router.get("/kpi-history/{city_name}")
async def get_kpi_history(
    city_name: str,
    metric: str = Query(..., description="Metric name"),
    days: int = Query(default=30, description="Number of days of history")
):
    """Get historical data for a specific KPI"""
    try:
        if city_name not in CITIES_DATA:
            raise HTTPException(status_code=404, detail=f"City '{city_name}' not found")
        
        # Generate mock historical data
        history = []
        base_value = CITIES_DATA[city_name].get(metric, {}).get("value", 100)
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=days-i)).strftime("%Y-%m-%d")
            # Add some random variation
            value = base_value * (1 + random.uniform(-0.1, 0.1))
            history.append({
                "date": date,
                "value": round(value, 2)
            })
        
        return {
            "city": city_name,
            "metric": metric,
            "history": history,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching KPI history: {str(e)}")

def _get_metric_category(metric_name: str) -> str:
    """Categorize metrics"""
    categories = {
        "air_quality": "Environment",
        "water_usage": "Resources",
        "energy_consumption": "Resources",
        "waste_recycled": "Environment",
        "population": "Demographics",
        "green_spaces": "Environment",
        "public_transport": "Transportation",
        "carbon_footprint": "Environment"
    }
    return categories.get(metric_name, "General")

def _generate_city_alerts(city_name: str, city_data: Dict) -> List[Dict[str, Any]]:
    """Generate mock alerts for a city"""
    alerts = []
    
    # Air quality alert
    if city_data.get("air_quality", {}).get("value", 0) > 40:
        alerts.append({
            "type": "warning",
            "category": "Environment",
            "message": f"Air quality in {city_name} is approaching unhealthy levels",
            "metric": "Air Quality Index",
            "value": city_data["air_quality"]["value"],
            "threshold": 40,
            "timestamp": datetime.now().isoformat()
        })
    
    # Energy consumption alert
    energy_trend = city_data.get("energy_consumption", {}).get("trend", "")
    if "+" in energy_trend and int(energy_trend.replace("+", "").replace("%", "")) > 3:
        alerts.append({
            "type": "info",
            "category": "Resources",
            "message": f"Energy consumption in {city_name} is increasing rapidly",
            "metric": "Energy Consumption",
            "trend": energy_trend,
            "timestamp": datetime.now().isoformat()
        })
    
    # Positive alert for recycling
    recycling_rate = city_data.get("waste_recycled", {}).get("value", 0)
    if recycling_rate > 80:
        alerts.append({
            "type": "success",
            "category": "Environment",
            "message": f"{city_name} has achieved excellent recycling rates!",
            "metric": "Waste Recycled",
            "value": f"{recycling_rate}%",
            "timestamp": datetime.now().isoformat()
        })
    
    return alerts
