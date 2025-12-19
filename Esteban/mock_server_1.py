from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from datetime import datetime, timezone
import random

app = FastAPI(title="Mock Thermal Environment Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

class Metric(BaseModel):
    timestamp: str
    unit_system: str
    location: str
    globe_temp_c: float
    dry_bulb_c: float
    wet_bulb_c: float
    air_velocity_ms: float
    relative_humidity_pct: float
    mrt_c: float
    wbgt_outdoor_c: float
    wbgt_indoor_c: float

def clamp(x, lo, hi): return max(lo, min(hi, x))

def sample_point(location="mock-cell-1"):
    Ta = random.uniform(24.0, 36.0)
    base_rh = random.uniform(40, 70) - 0.3 * (Ta - 30)
    RH = clamp(base_rh + random.uniform(-3, 3), 30, 85)
    delta = clamp(8 - (RH - 30) * 0.06, 1.0, 8.0)
    Tnw = clamp(Ta - random.uniform(delta * 0.6, delta), 10, Ta)
    solar = random.random()
    Tg = clamp(Ta + random.uniform(-1.0, 1.0) + solar * random.uniform(1.0, 8.0), Ta - 2.0, Ta + 10.0)
    mrt = clamp(Ta + solar * (Tg - Ta) * random.uniform(0.6, 0.9), Ta - 2, Ta + 12)
    Va = round(random.uniform(0.05, 1.5), 2)
    wbgt_out = 0.7 * Tnw + 0.2 * Tg + 0.1 * Ta
    wbgt_in  = 0.7 * Tnw + 0.3 * Ta
    return Metric(
        timestamp=datetime.now(timezone.utc).isoformat(),
        unit_system="SI",
        location=location,
        globe_temp_c=round(Tg, 2),
        dry_bulb_c=round(Ta, 2),
        wet_bulb_c=round(Tnw, 2),
        air_velocity_ms=Va,
        relative_humidity_pct=round(RH, 1),
        mrt_c=round(mrt, 2),
        wbgt_outdoor_c=round(wbgt_out, 2),
        wbgt_indoor_c=round(wbgt_in, 2),
    )

@app.get("/metrics", response_model=List[Metric])
def get_metrics(
    n: int = Query(1, ge=1, le=100),
    location: str = Query("mock-cell-1"),
):
    return [sample_point(location=location) for _ in range(n)]
