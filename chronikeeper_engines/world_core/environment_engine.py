# ============================================================
# ChroniKeeper – Environment Engine v4
# Time hub + climate + map microclimate + weather events
# ============================================================

import math
import random

# ----- baselines -----
CLIMATE_BASELINES = {
    "temperate": {"temperature": 0.5, "humidity": 0.5, "precipitation": 0.25, "air_quality": 0.8},
    "arid":      {"temperature": 0.75, "humidity": 0.15, "precipitation": 0.02, "air_quality": 0.85},
    "polar":     {"temperature": 0.20, "humidity": 0.40, "precipitation": 0.20, "air_quality": 0.85},
    "tropical":  {"temperature": 0.80, "humidity": 0.80, "precipitation": 0.60, "air_quality": 0.75}
}

SEASON_MODIFIERS = {
    "spring": {"temperature": +0.05, "humidity": +0.05, "precipitation": +0.05},
    "summer": {"temperature": +0.18, "humidity": 0.0,   "precipitation": -0.05},
    "autumn": {"temperature": -0.05, "humidity": +0.05, "precipitation": +0.05},
    "winter": {"temperature": -0.28, "humidity": 0.0,   "precipitation": +0.05}
}

# season → how fast weather clears
SEASON_FADE_MODIFIERS = {
    "spring": 0.7,   # smoother
    "summer": 1.0,   # fast clear after downpour
    "autumn": 0.8,   # medium
    "winter": 0.4    # slow lingering
}

# season → natural weather spawn bias (used later when auto mode on)
SEASON_WEATHER_BIAS = {
    "spring": {"fog": 0.04, "rain": 0.05, "storm": 0.02},
    "summer": {"rain": 0.06, "storm": 0.04, "heatwave": 0.03},
    "autumn": {"fog": 0.03, "rain": 0.04, "storm": 0.02},
    "winter": {"fog": 0.04, "snow": 0.05}
}

def _clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))

class EnvironmentEngine:
    """
    v4 – central time hub + environment + weather events.
    - keeps its own clock (day/hour/month/season)
    - reads map microclimate (heat_retention, airflow, water_coverage, elevation, comfort)
    - supports test flags to force weather (storm/fog/rain/heatwave)
    - event fade speed is influenced by: season + airflow + heat + water + elevation
    - outputs web/UI friendly fields (incl. wind_kmh)
    """

    def __init__(self, seed=None, map_manager=None):
        self.random = random.Random(seed)
        self.map_manager = map_manager

        # time hub
        self.time_state = {
            "day": 1,
            "hour": 12.0,
            "day_of_year": 120,
            "month": 4,
            "year": 1,
            "is_night": False,
        }
        self.hemisphere = "north"
        self.latitude = 45.0

        # smoothing
        self.prev_temperature = 0.5

        # weather/event state
        self.active_events = []      # list of {"type":..., "duration":..., "fade":..., "effects":{...}, "test":bool}
        self.test_flags = []         # names of forced events
        self.auto_weather_enabled = False  # later can be True
        self.current_fade_speed = 1.0

        # last signature
        self.signature = {}
        # --- Time control buffer for LLM synchronization ---
        self._pending_hours = 0.0
        self._total_elapsed_hours = 0.0
        self.lag_tolerance = 0.05  # ~3 min grace before auto-commit

    # =========================================================
    # TIME
    # =========================================================
    def set_hour(self, hour: float):
        self.time_state["hour"] = hour % 24
        self._update_day_night()

    def advance_time(self, hours: float = 1.0):
        """Advance world time forward by N hours (supports fractions)."""
        h = self.time_state["hour"] + hours
        while h >= 24.0:
            h -= 24.0
            self._advance_day()
        self.time_state["hour"] = h
        self._update_day_night()


    def _advance_day(self):
        self.time_state["day"] += 1
        self.time_state["day_of_year"] += 1
        if self.time_state["day_of_year"] > 360:
            self.time_state["day_of_year"] = 1
            self.time_state["year"] += 1
            # reset month correctly for the new year
            self.time_state["month"] = 1

    def _update_month(self):
        self.time_state["month"] = int(self.time_state["day_of_year"] / 30.0) + 1
        if self.time_state["month"] > 12:
            self.time_state["month"] = 12

    def _update_day_night(self):
        hr = self.time_state["hour"]
        self.time_state["is_night"] = not (6 <= hr < 18)

    def get_time_status(self):
        return self.time_state.copy()

    def get_season(self):
        m = self.time_state["month"]

        # Wrap month correctly
        if m < 1:
            m = 1
        elif m > 12:
            m = ((m - 1) % 12) + 1
            self.time_state["month"] = m

        if self.hemisphere == "north":
            if 3 <= m <= 5:
                return "spring"
            elif 6 <= m <= 8:
                return "summer"
            elif 9 <= m <= 11:
                return "autumn"
            else:
                return "winter"
        else:  # southern hemisphere reversed
            if 3 <= m <= 5:
                return "autumn"
            elif 6 <= m <= 8:
                return "winter"
            elif 9 <= m <= 11:
                return "spring"
            else:
                return "summer"
    
    # =========================================================
    # TIME BUFFER CONTROL (LLM / USER SAFETY)
    # =========================================================
    def request_time(self, hours: float):
        """Queue a time delta (fractions allowed) without committing yet."""
        self._pending_hours += hours
        print(f"[TIME] Pending +{hours:.2f}h (total pending {self._pending_hours:.2f})")

    def commit_time(self):
        """Commit pending time progression; advances the clock and environment."""
        if self._pending_hours <= 0.0:
            return
        delta = self._pending_hours
        self.advance_time(delta)
        self._pending_hours = 0.0
        self._total_elapsed_hours += delta
        print(f"[TIME] Committed +{delta:.2f}h (total elapsed {self._total_elapsed_hours:.2f}h)")

    def rollback_time(self):
        """Cancel any pending time progression (e.g., LLM regeneration or user edit)."""
        if self._pending_hours > 0.0:
            print(f"[TIME] Rollback: canceled {self._pending_hours:.2f}h pending.")
        self._pending_hours = 0.0

    def force_time_jump(self, hours: float):
        """Immediate, unconditional time advance (skip day, travel, etc.)."""
        self.advance_time(hours)
        self._total_elapsed_hours += hours
        print(f"[TIME] Forced advance {hours:.2f}h.")

    def graceful_tick(self, hours: float):
        """Small background drift—if AI hesitates too long, let time move slightly."""
        if self._pending_hours >= self.lag_tolerance:
            self.commit_time()
        else:
            self._pending_hours += hours * 0.5  # slow creep

    def get_moon_phase(self):
        """Return a tuple (phase_name, light_factor)."""
        phase_names = [
            "New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
            "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"
        ]
        day_index = self.time_state.get("day_of_year", 0) % 29
        phase_index = int((day_index / 29) * 8)
        phase_name = phase_names[phase_index]
        # Light factor roughly scaled by phase
        light_curve = [0.05, 0.15, 0.3, 0.5, 1.0, 0.5, 0.3, 0.15]
        return phase_name, light_curve[phase_index]


    # =========================================================
    # TEST FLAGS / EVENT CONTROL
    # =========================================================
    def set_test_flag(self, event_type: str, duration: int = 6):
        """Force an event regardless of random spawn."""
        ev = self._build_event(event_type, duration, test=True)
        if ev:
            self.active_events.append(ev)

    def clear_test_flags(self):
        """Remove all test events and normal events."""
        self.active_events = []
        self.test_flags = []

    def _build_event(self, event_type: str, duration: int, test: bool = False):
        """Create a standard event definition."""
        effects = {}
        event_type = event_type.lower()

        if event_type == "storm":
            effects = {
                "precipitation": +0.40,
                "visibility": -0.60,
                "comfort": -0.30,
                "airflow": +0.30,
                "noise": +0.20,
            }
        elif event_type == "rain":
            effects = {
                "precipitation": +0.20,
                "visibility": -0.30,
                "comfort": -0.10,
                "air_quality": +0.05,
            }
        elif event_type == "fog":
            effects = {
                "visibility": -0.50,
                "comfort": -0.10,
                "airflow": -0.20,
            }
        elif event_type == "heatwave":
            effects = {
                "temperature": +0.25,
                "comfort": -0.30,
                "air_quality": -0.20,
                "airflow": -0.10,
            }
        elif event_type == "clear":
            # special – remove all
            self.clear_test_flags()
            return None
        else:
            return None

        return {
            "type": event_type,
            "duration": duration,
            "fade": 1.0,
            "effects": effects,
            "test": test,
        }

    # =========================================================
    # MAIN UPDATE
    # =========================================================
    def update(self, world_state=None):        
        # -----------------------------------------------------
        # Allow test world objects or raw dict contexts
        # -----------------------------------------------------
        if world_state is None:
            ctx = {}
        elif isinstance(world_state, dict):
            ctx = world_state
        elif hasattr(world_state, "context"):
            ctx = world_state.context
        else:
            ctx = {}
               
        season = self.get_season()
        climate = getattr(world_state, "climatic_zone", "temperate") if world_state else "temperate"
        hour = self.time_state["hour"]

        # Calculate simulated hours passed since last update
        if not hasattr(self, "_last_update_hour"):
            self._last_update_hour = hour
        elapsed_hours = (hour - self._last_update_hour) % 24.0
        self._last_update_hour = hour

        # Convert to fractional days (used for fading & smoothing)
        elapsed_frac_day = elapsed_hours / 24.0



        # --- base from climate + season
        base = CLIMATE_BASELINES.get(climate, CLIMATE_BASELINES["temperate"]).copy()
        seas = SEASON_MODIFIERS.get(season, {})
        for k, v in seas.items():
            if k in base:
                base[k] = _clamp(base[k] + v)

        # --- diurnal
        diurnal_amp = 0.08
        if climate == "arid":
            diurnal_amp = 0.12
        diurnal = math.sin((hour / 24.0) * math.pi * 2) * diurnal_amp
        raw_temp_base = _clamp(base["temperature"] + diurnal)

        # --- map context
        # keep any latitude or test-supplied context values
        if not isinstance(ctx, dict):
            ctx = {}

        location_id = getattr(world_state, "location_id", None) if world_state else None
        map_ctx = {}
        if self.map_manager and location_id:
            map_ctx = self.map_manager.get_context_fragment(location_id)

        # merge, with test ctx taking priority
        ctx = {**map_ctx, **ctx}
        location_id = getattr(world_state, "location_id", None) if world_state else None
        if self.map_manager and location_id:
            ctx = self.map_manager.get_context_fragment(location_id)
        heat_ret = float(ctx.get("heat_retention", 0.0))
        airflow  = float(ctx.get("airflow", 0.5))
        water    = float(ctx.get("water_coverage", 0.0))
        elev     = float(ctx.get("elevation", 0.0))
        comfort_mod = float(ctx.get("comfort", 0.0))
        local_airq  = float(ctx.get("air_quality", 0.0))
        base_noise  = float(ctx.get("noise", 0.3))

        # --- precipitation interplay
        precip = _clamp(base.get("precipitation", 0.0))
        precip_temp_shift = -precip * 0.06
        precip_airq_shift = +precip * 0.03

        # --- local heat vs airflow
        raw_temperature = _clamp(raw_temp_base + heat_ret * (1 - airflow) + precip_temp_shift)

        # --- retention smoothing
        norm_ret = _clamp(heat_ret, -0.2, 0.6)
        memory_weight = 0.7 + norm_ret * 0.3
        new_weight = 1.0 - memory_weight
        temperature = self.prev_temperature * memory_weight + raw_temperature * new_weight
        self.prev_temperature = temperature

        # --- crowd/noise
        crowd = self._crowd_pattern(hour)
        noise = _clamp(base_noise + crowd * 0.4)

        # =====================================================
        # GEOGRAPHIC + URBAN MICROCLIMATE ADJUSTMENTS
        # =====================================================

        latitude = float(ctx.get("latitude", self.latitude))
        day_of_year = self.time_state.get("day_of_year", 172)

        # --- Correct astronomical daylight model (now responsive to latitude) ---
        declination = 23.44 * math.sin(math.radians((360 / 365.0) * (day_of_year - 80)))
        lat_r = math.radians(latitude)
        dec_r = math.radians(declination)
        try:
            hour_angle = math.acos(-math.tan(lat_r) * math.tan(dec_r))
            daylight_hours = 24.0 * hour_angle / math.pi
        except ValueError:
            # Polar edge cases: full day or night
            daylight_hours = 24.0 if latitude * declination > 0 else 0.0

        # clamp + factor
        daylight_hours = _clamp(daylight_hours, 0.0, 24.0)
        daylight_factor = daylight_hours / 24.0

        # store for later use
        ctx["daylight_hours"] = round(daylight_hours, 2)
        ctx["daylight_factor"] = round(daylight_factor, 3)
        
        # =====================================================
        # LATITUDE + DAYLIGHT INFLUENCE ON TEMPERATURE / COMFORT
        # =====================================================

        # Temperature shift by latitude and season daylight
        # Lower latitudes stay warmer; higher → colder.
        # daylight_factor (0..1) shifts toward seasonal extremes.
        lat_temp_bias = _clamp(1.0 - abs(latitude) / 90.0, 0.2, 1.0)
        daylight_temp_bias = (daylight_factor - 0.5) * 0.25  # small ±0.125 swing
        seasonal_temp_adj = (lat_temp_bias * 0.3) + daylight_temp_bias

        # Blend into temperature smoothly
        temperature = _clamp(temperature + seasonal_temp_adj - 0.1)

        # Comfort also reacts to daylight length (psychological effect)
        comfort_mod += (daylight_factor - 0.5) * 0.2


        # --- anthropic modifiers ---
        settlement_size = float(ctx.get("settlement_size", 0.0))     # 0–5
        structure_density = float(ctx.get("structure_density", 0.0)) # 0–1
        wind_block = float(ctx.get("wind_block", 0.0))
        wind_redirect = float(ctx.get("wind_redirect", 0.0))
        noise_pollution = float(ctx.get("noise_pollution", 0.0))

        # --- urban heat island effect ---
        if self.time_state["is_night"]:
            heat_ret += 0.1 * structure_density + 0.05 * settlement_size
        else:
            heat_ret += 0.05 * structure_density  # reflective daytime warming

        # --- adjust airflow for blocked canyons or redirected winds ---
        airflow = airflow * (1.0 - wind_block) + wind_redirect * 0.3

        # --- humidity & comfort tweaks for dense areas ---
        humidity_mod = 1.0 - 0.2 * structure_density
        base["humidity"] *= humidity_mod
        comfort_mod *= 1.0 - (noise_pollution * 0.3)

        # --- optional: store daylight factor for diagnostics / UI ---
        ctx["daylight_hours"] = round(daylight_hours, 2)
        ctx["daylight_factor"] = round(daylight_factor, 3)

        # =====================================================
        # VISIBILITY COMPUTATION (natural + moon + pollution)
        # =====================================================

        # --- base humidity and weather visibility ---
        humidity = _clamp(base.get("humidity", 0.5) + precip * 0.15)
        # heavier humidity impact at night → darker, murkier air
        hum_factor = 0.5 if not self.time_state["is_night"] else 0.8
        atmo_visibility = _clamp(1.0 - humidity * hum_factor - precip * 0.4)

        # --- daylight curve (1.0 at noon → 0.0 at midnight) ---
        daylight_curve = 0.5 + 0.5 * math.cos(((hour - 12) / 12) * math.pi)
        daylight_curve = _clamp(daylight_curve, 0.0, 1.0)

        # --- seasonal bias (affects how bright seasons feel) ---
        season_vis_bias = {
            "summer": 0.35, "spring": 0.25, "autumn": 0.20, "winter": 0.10
        }.get(season, 0.2)

        # --- moonlight & map light pollution ---
        phase_name, moon_light = self.get_moon_phase()
        
        # --- approximate falloff of nearby settlement light ---
        # requires MapManager to supply settlement size (0=none, 1=hamlet, 2=village, 3=town, 4=city, 5=megacity)
        settlement_size = float(ctx.get("settlement_size", 0.0))
        dist_to_city = float(ctx.get("distance_to_city", 1.0))  # in map grid units (1.0 = local tile)

        # base light from settlement size (log-like growth)
        base_light = (settlement_size / 5.0) ** 1.2

        # exponential distance decay: near=1.0, far=~0.0
        distance_factor = math.exp(-1.5 * dist_to_city)

        # combined contribution
        settlement_light = base_light * distance_factor
        
        light_pollution = float(ctx.get("light_pollution", 0.0))
        light_pollution = _clamp(float(ctx.get("light_pollution", 0.0)) + settlement_light, 0.0, 1.0)

        # --- total illumination factor (0 = pitch dark, 1 = bright daylight) ---
        if self.time_state["is_night"]:
            # combine moonlight, pollution, and a faint twilight term
            illumination = _clamp(moon_light * 0.5 + light_pollution * 1.2 + daylight_curve * 0.3, 0.0, 1.0)
        else:
            illumination = _clamp(daylight_curve + light_pollution * 0.2, 0.0, 1.0)

        # --- minimal light floor (darker winters, brighter summers) ---
        min_visibility = 0.02 + season_vis_bias * (illumination * 0.5)

        # --- combine atmosphere and lighting limits ---
        # darker nights: scale atmospheric clarity more strongly by light level
        # so new-moon rural areas can reach 0.03–0.06
        darkness_weight = 0.15 + illumination * 0.6          # 0.15 at night → 0.75 at noon
        visibility = _clamp(atmo_visibility * darkness_weight, 0.0, 1.0)

        # ensure a minimal floor so fog/rain don't clamp to zero
        visibility = max(visibility, min_visibility * 0.8)

        # --- air quality base
        air_quality = _clamp(base.get("air_quality", 0.8) + local_airq + precip_airq_shift - noise * 0.08)

        # =====================================================
        #  APPLY WEATHER EVENTS (storm, fog, rain, heatwave)
        # =====================================================

        # compute seasonal + area tug fade speed
        season_fade = SEASON_FADE_MODIFIERS.get(season, 1.0)
        fade_mod = (
            0.6                  # base
            - airflow * 0.25     # windy → clears faster
            + heat_ret * 0.25    # hot/urban → lingers
            + water * 0.20       # coastal → lingers
            - elev * 0.10        # mountains → clears faster
        )
        fade_mod = _clamp(fade_mod, 0.2, 1.2)
        fade_speed = season_fade * fade_mod
        self.current_fade_speed = fade_speed

        # optionally spawn auto weather (later when enabled)
        if self.auto_weather_enabled:
            self._maybe_spawn_auto_event(season, water, airflow, elev)

        # apply + decay events
        active_event_names = []
        max_event_intensity = 0.0

        still_active = []
        for ev in self.active_events:
            # scale effects by current fade
            intensity = _clamp(ev["fade"], 0.0, 1.0)
            if intensity > 0.01:
                for key, delta in ev["effects"].items():
                    # additive, scaled by intensity
                    if key == "temperature":
                        temperature = _clamp(temperature + delta * intensity)
                    elif key == "precipitation":
                        precip = _clamp(precip + delta * intensity)
                    elif key == "visibility":
                        visibility = _clamp(visibility + delta * intensity)
                    elif key == "comfort":
                        comfort_mod += delta * intensity
                    elif key == "airflow":
                        airflow = _clamp(airflow + delta * intensity)
                    elif key == "air_quality":
                        air_quality = _clamp(air_quality + delta * intensity)
                    elif key == "noise":
                        noise = _clamp(noise + delta * intensity)

                active_event_names.append(ev["type"])
                max_event_intensity = max(max_event_intensity, intensity)

            # =====================================================
            # Realistic storm/fog fade: build-up → peak → drizzle-out
            # =====================================================

            # Decrease remaining duration
            ev["duration"] -= 1

            # Dynamic easing factor: exponential-style decay that slows near 0
            # Fade speed still obeys season + area tug
            if ev["type"] == "storm":
                # storms fade exponentially (quick start, long tail)
                ev["fade"] *= (0.85 ** fade_speed)
            # Time-aware fade that scales by simulated hours elapsed

            # storms fade exponentially (quick start, long tail)
            if ev["type"] == "storm":
                ev["fade"] *= (0.85 ** (fade_speed * elapsed_hours))
            elif ev["type"] in ("rain", "fog", "snow"):
                ev["fade"] -= 0.08 * fade_speed * elapsed_hours
            else:
                ev["fade"] *= (0.90 ** (fade_speed * elapsed_hours))


        # --- comfort final
        comfort = _clamp(1.0 - abs(temperature - 0.5) * 1.2 - precip * 0.3 + comfort_mod)

        # --- safety
        safety = _clamp(1.0 - noise * 0.18 - (1.0 - air_quality) * 0.25 - self._night_safety_penalty(hour))

        # --- wind: from airflow + events
        # airflow (0..1) → wind_strength (0.1..1)
        wind_strength = _clamp(0.1 + airflow * 0.9, 0.0, 1.0)
        # storm/fog/rain can also affect wind (already applied above)
        wind_kmh = round(wind_strength * 45.0, 1)  # 0..45 km/h approx

        sig = {
            "temperature": round(temperature, 3),
            "humidity": round(humidity, 3),
            "precipitation": round(precip, 3),
            "comfort": round(comfort, 3),
            "air_quality": round(air_quality, 3),
            "visibility": round(visibility, 3),
            "safety": round(safety, 3),
            "noise": round(noise, 3),
            "wind_strength": round(wind_strength, 3),
            "wind_kmh": wind_kmh,
            "heat_retention": round(heat_ret, 3),
            "airflow": round(airflow, 3),
            "hour": round(hour, 2),
            "day": self.time_state["day"],
            "month": self.time_state["month"],
            "season": season,
            "is_night": self.time_state["is_night"],
            "active_events": active_event_names,
            "event_intensity": round(max_event_intensity, 3),
            "event_fade_speed": round(fade_speed, 3),
            "local_context": ctx,
            "moon_phase": phase_name,
            "moon_light": round(moon_light, 3),
        }
        
        self.signature = sig

        # Graceful assignment for dicts OR object-style containers
        if world_state is not None:
            if isinstance(world_state, dict):
                world_state["environment_signature"] = sig
            else:
                setattr(world_state, "environment_signature", sig)

        return {
            "ctx": ctx,
            **sig
        }


    # =========================================================
    # HELPERS
    # =========================================================
    def _crowd_pattern(self, hour):
        if 7 <= hour < 9: return 0.5
        if 9 <= hour < 17: return 1.0
        if 17 <= hour < 21: return 0.9
        return 0.25

    def _night_safety_penalty(self, hour):
        if 0 <= hour < 6: return 0.08
        if 22 <= hour < 24: return 0.04
        return 0.0

    def _maybe_spawn_auto_event(self, season, water, airflow, elev):
        """Very light auto-mode; can be extended later."""
        bias = SEASON_WEATHER_BIAS.get(season, {})
        # coastal → more fog/rain
        if water > 0.6 and self.random.random() < bias.get("fog", 0.0) + 0.01:
            ev = self._build_event("fog", duration=3)
            if ev: self.active_events.append(ev)
        if water > 0.6 and self.random.random() < bias.get("rain", 0.0):
            ev = self._build_event("rain", duration=4)
            if ev: self.active_events.append(ev)
        # mountains → storms
        if elev > 0.7 and self.random.random() < bias.get("storm", 0.0):
            ev = self._build_event("storm", duration=4)
            if ev: self.active_events.append(ev)
