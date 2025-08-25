from __future__ import annotations

from typing import Callable, Dict, Any, List

from horary_config import cfg
from .calculation.helpers import days_to_sign_exit
from .reception import TraditionalReceptionCalculator
try:
    from ..models import Planet, Aspect, HoraryChart
except ImportError:  # pragma: no cover - fallback when executed as script
    from models import Planet, Aspect, HoraryChart

CLASSICAL_PLANETS: List[Planet] = [
    Planet.SUN,
    Planet.MOON,
    Planet.MERCURY,
    Planet.VENUS,
    Planet.MARS,
    Planet.JUPITER,
    Planet.SATURN,
]

ASPECT_TYPES: List[Aspect] = [
    Aspect.CONJUNCTION,
    Aspect.SEXTILE,
    Aspect.SQUARE,
    Aspect.TRINE,
    Aspect.OPPOSITION,
]


def verb(aspect: Aspect) -> str:
    """Return the verb form for a given aspect."""
    mapping = {
        Aspect.CONJUNCTION: "conjoins",
        Aspect.SEXTILE: "sextiles",
        Aspect.SQUARE: "squares",
        Aspect.TRINE: "trines",
        Aspect.OPPOSITION: "opposes",
    }
    return mapping.get(aspect, f"{aspect.display_name.lower()}s")


def check_future_prohibitions(
    chart: HoraryChart,
    sig1: Planet,
    sig2: Planet,
    days_ahead: float,
    calc_aspect_time: Callable[[Any, Any, Aspect, float, float], float],
) -> Dict[str, Any]:
    """Scan for intervening aspects before a main perfection.

    Parameters
    ----------
    chart : HoraryChart
        Chart containing planetary positions.
    sig1, sig2 : Planet
        Significators forming the main perfection.
    days_ahead : float
        Time until the main perfection in days.
    calc_aspect_time : callable
        Function for computing signed time to an aspect. Positive values are
        future contacts while negative values indicate a recent separation.
    """

    config = cfg()
    require_in_sign = getattr(getattr(config, "perfection", {}), "require_in_sign", True)
    allow_out_of_sign = getattr(getattr(config, "perfection", {}), "allow_out_of_sign", False)

    pos1 = chart.planets[sig1]
    pos2 = chart.planets[sig2]
    reception_calc = TraditionalReceptionCalculator()

    def _valid(t: float, p_a, p_b) -> bool:
        if t is None or t <= 0 or t >= days_ahead:
            return False
        if require_in_sign and not allow_out_of_sign:
            exit_a = days_to_sign_exit(p_a.longitude, p_a.speed)
            exit_b = days_to_sign_exit(p_b.longitude, p_b.speed)
            return t < exit_a and t < exit_b
        return True

    events: List[Dict[str, Any]] = []

    for planet in CLASSICAL_PLANETS:
        if planet in (sig1, sig2):
            continue
        p_pos = chart.planets.get(planet)
        if not p_pos:
            continue

        for aspect in ASPECT_TYPES:
            t1 = calc_aspect_time(pos1, p_pos, aspect, chart.julian_day, days_ahead)
            t2 = calc_aspect_time(pos2, p_pos, aspect, chart.julian_day, days_ahead)

            valid1 = _valid(t1, pos1, p_pos)
            valid2 = _valid(t2, pos2, p_pos)
            if valid1 and valid2:
                if (t1 < 0 < t2) or (t2 < 0 < t1):
                    t_event = t2 if t2 > 0 else t1
                    if abs(p_pos.speed) > max(abs(pos1.speed), abs(pos2.speed)):
                        quality = (
                            "easier"
                            if aspect in (Aspect.CONJUNCTION, Aspect.TRINE, Aspect.SEXTILE)
                            else "with difficulty"
                        )
                        rec1 = reception_calc.calculate_comprehensive_reception(chart, planet, sig1)
                        rec2 = reception_calc.calculate_comprehensive_reception(chart, planet, sig2)
                        has_reception = rec1["type"] != "none" or rec2["type"] != "none"
                        reason = (
                            f"Perfection by translation ({aspect.display_name.lower()}): positive "
                            + (f"({quality})" if quality == "easier" else f"{quality}")
                        )
                        if has_reception and quality == "with difficulty":
                            reason += " (softened by reception)"
                        events.append(
                            {
                                "t": t_event,
                                "payload": {
                                    "prohibited": False,
                                    "type": "translation",
                                    "translator": planet,
                                    "t_event": t_event,
                                    "aspect": aspect,
                                    "quality": quality,
                                    "reception": has_reception,
                                    "reason": reason,
                                },
                            }
                        )
                else:
                    t_first, t_second = (t1, t2) if t1 <= t2 else (t2, t1)
                    if (
                        t_first < t_second
                        and t_first >= 0
                        and abs(p_pos.speed) > max(abs(pos1.speed), abs(pos2.speed))
                    ):
                        t_event = t_second
                        quality = (
                            "easier"
                            if aspect in (Aspect.CONJUNCTION, Aspect.TRINE, Aspect.SEXTILE)
                            else "with difficulty"
                        )
                        rec1 = reception_calc.calculate_comprehensive_reception(chart, planet, sig1)
                        rec2 = reception_calc.calculate_comprehensive_reception(chart, planet, sig2)
                        has_reception = rec1["type"] != "none" or rec2["type"] != "none"
                        reason = (
                            f"Perfection by translation ({aspect.display_name.lower()}): positive "
                            + (f"({quality})" if quality == "easier" else f"{quality}")
                        )
                        if has_reception and quality == "with difficulty":
                            reason += " (softened by reception)"
                        events.append(
                            {
                                "t": t_event,
                                "payload": {
                                    "prohibited": False,
                                    "type": "translation",
                                    "translator": planet,
                                    "t_event": t_event,
                                    "aspect": aspect,
                                    "quality": quality,
                                    "reception": has_reception,
                                    "reason": reason,
                                },
                            }
                        )
                    elif (
                        t_first < t_second
                        and t_first >= 0
                        and abs(p_pos.speed) < min(abs(pos1.speed), abs(pos2.speed))
                    ):
                        t_event = t_second
                        quality = (
                            "easier"
                            if aspect in (Aspect.CONJUNCTION, Aspect.TRINE, Aspect.SEXTILE)
                            else "with difficulty"
                        )
                        rec1 = reception_calc.calculate_comprehensive_reception(chart, planet, sig1)
                        rec2 = reception_calc.calculate_comprehensive_reception(chart, planet, sig2)
                        has_reception = rec1["type"] != "none" or rec2["type"] != "none"
                        reason = (
                            f"Perfection by collection ({aspect.display_name.lower()}): positive "
                            + (f"({quality})" if quality == "easier" else f"{quality}")
                        )
                        if has_reception and quality == "with difficulty":
                            reason += " (softened by reception)"
                        events.append(
                            {
                                "t": t_event,
                                "payload": {
                                    "prohibited": False,
                                    "type": "collection",
                                    "collector": planet,
                                    "t_event": t_event,
                                    "aspect": aspect,
                                    "quality": quality,
                                    "reception": has_reception,
                                    "reason": reason,
                                },
                            }
                        )
                    else:
                        if t1 > 0 and (t1 <= t2 or t2 <= 0):
                            events.append(
                                {
                                    "t": t1,
                                    "payload": {
                                        "prohibited": True,
                                        "type": "prohibition",
                                        "prohibitor": planet,
                                        "significator": sig1,
                                        "t_prohibition": t1,
                                        "reason": f"{planet.value} {verb(aspect)} {sig1.value} before perfection",
                                    },
                                }
                            )
                        elif t2 > 0 and (t2 < t1 or t1 <= 0):
                            events.append(
                                {
                                    "t": t2,
                                    "payload": {
                                        "prohibited": True,
                                        "type": "prohibition",
                                        "prohibitor": planet,
                                        "significator": sig2,
                                        "t_prohibition": t2,
                                        "reason": f"{planet.value} {verb(aspect)} {sig2.value} before perfection",
                                    },
                                }
                            )
            elif valid1 and t1 > 0:
                events.append(
                    {
                        "t": t1,
                        "payload": {
                            "prohibited": True,
                            "type": "prohibition",
                            "prohibitor": planet,
                            "significator": sig1,
                            "t_prohibition": t1,
                            "reason": f"{planet.value} {verb(aspect)} {sig1.value} before perfection",
                        },
                    }
                )
            elif valid2 and t2 > 0:
                events.append(
                    {
                        "t": t2,
                        "payload": {
                            "prohibited": True,
                            "type": "prohibition",
                            "prohibitor": planet,
                            "significator": sig2,
                            "t_prohibition": t2,
                            "reason": f"{planet.value} {verb(aspect)} {sig2.value} before perfection",
                        },
                    }
                )

    if events:
        return min(events, key=lambda e: e["t"])["payload"]
    return {"prohibited": False, "type": "none", "reason": "No prohibitions detected"}
