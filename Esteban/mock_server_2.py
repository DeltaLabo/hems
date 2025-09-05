from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from collections import deque
from functools import lru_cache
import asyncio, random, os, json, re

# ====== Importa tus funciones de índices ======
# Asegúrate de que Funciones.py está junto a este archivo.
from Funciones import (
    indice_de_sudoracion,          # (Ta, Tg, Tnw, iclo, M, Va, postura, aclimatacion, conveccion)
    tgbh,                          # (radiacion_solar, Ta, Tg, Tnw, cavs, M, aclimatacion)
    indice_sobrecarga_calorica     # (M, Va, Tg, Ta, Tnw, iclo, altura, peso)
)

# ====== Config ======
SAMPLE_EVERY_SECONDS = int(os.getenv("SAMPLE_EVERY_SECONDS", "60"))       # 1 muestra/min
HISTORY_MAX_POINTS   = int(os.getenv("HISTORY_MAX_POINTS", str(60*24*7))) # ~7 días a 1/min
PROFILE_DIR          = os.getenv("PROFILE_DIR", "profiles")
LOCATION_DEFAULT     = os.getenv("LOCATION_DEFAULT", "mock-cell-1")

# ====== App ======
app = FastAPI(title="Mock Thermal Server (per-user indices via Funciones.py)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ====== Modelos ======
class RawMetric(BaseModel):
    timestamp: str
    ts_ms: int
    unit_system: str
    location: str
    # Variables ambientales generadas por el servidor
    dry_bulb_c: float           # Ta
    wet_bulb_c: float           # Tnw
    globe_temp_c: float         # Tg
    air_velocity_ms: float      # Va
    # RH la dejamos opcional por si quieres usarla luego
    relative_humidity_pct: float

class Indices(BaseModel):
    # --- Resultados de tus funciones ---
    # tgbh:
    wbgt_c: float
    wbgt_efectivo_c: float
    wbgt_referencia_c: float
    estado_wbgt: str
    # indice_de_sudoracion:
    dle_alarma_q_min: float
    dle_peligro_q_min: float
    dle_alarma_d_min: float
    dle_peligro_d_min: float
    # indice_sobrecarga_calorica:
    isc_pct: float
    isc_clasificacion: str
    tiempo_exp_per_min: float
    tiempo_recuperacion_min: float
    evaporacion_max: float
    evaporacion_req: float

    # (opcional) eco de variables de perfil utilizadas (útil para trazabilidad)
    perfil_usado: Dict[str, Any]

class OutMetric(RawMetric):
    user: str
    indices: Indices

# ====== Buffer de histórico ======
buffer: deque[RawMetric] = deque(maxlen=HISTORY_MAX_POINTS)

# ====== Utilidades ======
def clamp(x, lo, hi): 
    return max(lo, min(hi, x))

def _parse_txt_profile(text: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^\s*([A-Za-z0-9_]+)\s*=\s*(.+?)\s*$", line)
        if not m:
            continue
        k, v = m.group(1), m.group(2)
        v_lower = v.lower()
        if v_lower in ("true", "false", "si", "no"):
            # conserva "Si"/"No" literal si lo usas así en tus funciones
            out[k] = "Si" if v_lower in ("true", "si") else "No"
        else:
            try:
                out[k] = float(v)
            except ValueError:
                out[k] = v
    return out

@lru_cache(maxsize=128)
def load_profile(user: str) -> Dict[str, Any]:
    """
    Busca profiles/<user>.json o .txt; si no, profiles/default.json.
    Cachea hasta reiniciar el proceso.
    """
    paths = [
        os.path.join(PROFILE_DIR, f"{user}.json"),
        os.path.join(PROFILE_DIR, f"{user}.txt"),
        os.path.join(PROFILE_DIR, "default.json"),
    ]
    for p in paths:
        if os.path.isfile(p):
            try:
                if p.endswith(".json"):
                    with open(p, "r", encoding="utf-8") as f:
                        return json.load(f)
                else:
                    with open(p, "r", encoding="utf-8") as f:
                        return _parse_txt_profile(f.read())
            except Exception:
                continue
    # Fallback mínimo
    return {
        "iclo": 0.6,
        "carga_metabolica": 200,
        "postura": "De pie",
        "aclimatacion": "Si",
        "conveccion": "Natural",
        "radiacion_solar": "No",
        "cavs": 0.0,
        "altura": 1.70,
        "peso": 70
    }

def sample_raw(location: str = LOCATION_DEFAULT) -> RawMetric:
    # RANGOS por defecto; ajusta a tu caso (cleanroom, etc.)
    Ta = random.uniform(24.0, 36.0)
    # RH acotada y muy simple (solo para trazar si la quieres)
    base_rh = random.uniform(40, 70) - 0.3 * (Ta - 30)
    RH = clamp(base_rh + random.uniform(-3, 3), 30, 85)
    # Tnw ≤ Ta (delta depende de RH)
    delta = clamp(8 - (RH - 30) * 0.06, 1.0, 8.0)
    Tnw = clamp(Ta - random.uniform(delta * 0.6, delta), 10, Ta)
    # Tg: aprox con “solar” aleatorio; si es indoor puro, fija solar=0 y Tg≈Ta
    solar = random.random()
    Tg = clamp(Ta + random.uniform(-1.0, 1.0) + solar * random.uniform(1.0, 8.0), Ta - 2.0, Ta + 10.0)
    # Va:
    Va = round(random.uniform(0.05, 1.5), 2)

    now = datetime.now(timezone.utc)
    return RawMetric(
        timestamp=now.isoformat(),
        ts_ms=int(now.timestamp() * 1000),
        unit_system="SI",
        location=location,
        dry_bulb_c=round(Ta, 2),
        wet_bulb_c=round(Tnw, 2),
        globe_temp_c=round(Tg, 2),
        air_velocity_ms=Va,
        relative_humidity_pct=round(RH, 1),
    )

def compute_indices_with_profile(raw: RawMetric, profile: Dict[str, Any]) -> Indices:
    # Lee del perfil (con defaults si faltan)
    iclo           = profile.get("iclo", 0.6)
    M              = profile.get("carga_metabolica", 200)         # W (tu función divide entre 1.7)
    postura        = profile.get("postura", "De pie")             # "De pie" / "Sentado" / "Agachado"
    aclimatacion   = profile.get("aclimatacion", "Si")            # "Si" / "No"
    conveccion     = profile.get("conveccion", "Natural")         # "Natural" / "Forzada"
    radiacion_sol  = profile.get("radiacion_solar", "No")         # "Si" / "No"
    cavs           = profile.get("cavs", 0.0)
    altura         = profile.get("altura", 1.70)
    peso           = profile.get("peso", 70.0)

    # Alias de variables ambientales
    Ta  = raw.dry_bulb_c
    Tnw = raw.wet_bulb_c
    Tg  = raw.globe_temp_c
    Va  = raw.air_velocity_ms

    # ---- Llamadas a TUS funciones (tuplas -> dict) ----
    # 1) TGBH
    wbgt, wbgt_ef, wbgt_ref, estado = tgbh(radiacion_sol, Ta, Tg, Tnw, cavs, M, aclimatacion)

    # 2) Índice de sudoración (SWreq)
    dle_a_q, dle_p_q, dle_a_d, dle_p_d = indice_de_sudoracion(
        Ta, Tg, Tnw, iclo, M, Va, postura, aclimatacion, conveccion
    )

    # 3) Índice de sobrecarga calórica (ISC)
    isc, clasif, t_exp_per, t_rec, evap_max, evap_req = indice_sobrecarga_calorica(
        M, Va, Tg, Ta, Tnw, iclo, altura, peso
    )

    return Indices(
        wbgt_c=round(float(wbgt), 2),
        wbgt_efectivo_c=round(float(wbgt_ef), 2),
        wbgt_referencia_c=round(float(wbgt_ref), 2),
        estado_wbgt=str(estado),

        dle_alarma_q_min=float(dle_a_q),
        dle_peligro_q_min=float(dle_p_q),
        dle_alarma_d_min=float(dle_a_d),
        dle_peligro_d_min=float(dle_p_d),

        isc_pct=round(float(isc), 2),
        isc_clasificacion=str(clasif),
        tiempo_exp_per_min=float(t_exp_per) if t_exp_per != float("inf") else 1e12,   # evita NaN en gráficas
        tiempo_recuperacion_min=float(t_rec),
        evaporacion_max=float(evap_max),
        evaporacion_req=float(evap_req),

        perfil_usado={
            "iclo": iclo, "carga_metabolica": M, "postura": postura,
            "aclimatacion": aclimatacion, "conveccion": conveccion,
            "radiacion_solar": radiacion_sol, "cavs": cavs,
            "altura": altura, "peso": peso
        }
    )

def decorate(raw: RawMetric, user: str) -> OutMetric:
    profile = load_profile(user)
    indices = compute_indices_with_profile(raw, profile)
    return OutMetric(**raw.model_dump(), user=user, indices=indices)

# ====== Sampler asíncrono ======
async def sampler_loop():
    if not buffer:
        buffer.append(sample_raw())
    while True:
        await asyncio.sleep(SAMPLE_EVERY_SECONDS)
        buffer.append(sample_raw())

@app.on_event("startup")
async def on_startup():
    os.makedirs(PROFILE_DIR, exist_ok=True)
    asyncio.create_task(sampler_loop())

# ====== Endpoints ======
@app.get("/")
def root():
    return {
        "message": "Mock per-user running (Funciones.py)",
        "endpoints": [
            "/metrics?user=<name>",
            "/metrics/last?n=60&user=<name>",
            "/metrics/range?start_ms=..&end_ms=..&user=<name>"
        ],
        "sample_every_seconds": SAMPLE_EVERY_SECONDS,
        "buffer_capacity": HISTORY_MAX_POINTS,
        "profiles_dir": PROFILE_DIR
    }

@app.get("/metrics", response_model=OutMetric)
def latest(user: str = Query("default")):
    raw = buffer[-1] if buffer else sample_raw()
    return decorate(raw, user)

@app.get("/metrics/last", response_model=List[OutMetric])
def last_n(n: int = Query(1, ge=1, le=5000), user: str = Query("default")):
    data = list(buffer)
    chosen = data[-n:] if n < len(data) else data
    return [decorate(r, user) for r in chosen]

@app.get("/metrics/range", response_model=List[OutMetric])
def by_range(
    start_ms: Optional[int] = Query(None, description="epoch ms"),
    end_ms:   Optional[int] = Query(None, description="epoch ms"),
    user:     str = Query("default")
):
    if not buffer:
        return []
    data = list(buffer)
    if start_ms is None and end_ms is None:
        chosen = data
    else:
        if end_ms is None:
            end_ms = data[-1].ts_ms
        if start_ms is None:
            start_ms = end_ms - 60*60*1000  # última hora
        chosen = [m for m in data if start_ms <= m.ts_ms <= end_ms]
    return [decorate(r, user) for r in chosen]
