"""
Tests unitaires pour les fonctions de formatage de temps.
"""

from app.utils.time_format import format_time


def test_format_time_none():
    """Test que format_time retourne une chaîne vide pour None."""
    assert format_time(None) == ""


def test_format_time_minutes_only():
    """Test le formatage de minutes uniquement."""
    assert format_time(30) == "30min"
    assert format_time(45) == "45min"
    assert format_time(0) == "0min"


def test_format_time_hours_only():
    """Test le formatage d'heures uniquement (sans minutes)."""
    assert format_time(60) == "1h"
    assert format_time(120) == "2h"
    assert format_time(300) == "5h"


def test_format_time_hours_and_minutes():
    """Test le formatage d'heures et minutes."""
    assert format_time(90) == "1h30min"
    assert format_time(150) == "2h30min"
    assert format_time(75) == "1h15min"


def test_format_time_negative():
    """Test le formatage de valeurs négatives."""
    assert format_time(-30) == "-30min"
    assert format_time(-60) == "-1h"
    assert format_time(-90) == "-1h30min"


def test_format_time_float_hours():
    """Test le formatage de float représentant des heures (< 100)."""
    # 0.5 heures = 30 minutes
    assert format_time(0.5) == "30min"
    # 1.5 heures = 90 minutes
    assert format_time(1.5) == "1h30min"
    # 2.25 heures = 135 minutes
    assert format_time(2.25) == "2h15min"


def test_format_time_float_minutes():
    """Test le formatage de float représentant des minutes (> 100)."""
    # Si > 100, considéré comme déjà en minutes
    assert format_time(120.5) == "2h"
    # 90.7 < 100 donc traité comme heures: 90.7 * 60 = 5442 minutes = 90h42min
    assert format_time(90.7) == "90h42min"


def test_format_time_large_values():
    """Test le formatage de grandes valeurs."""
    assert format_time(480) == "8h"  # 8 heures
    assert format_time(495) == "8h15min"  # 8h15
    assert format_time(1440) == "24h"  # 24 heures


def test_format_time_edge_cases():
    """Test les cas limites."""
    assert format_time(1) == "1min"
    assert format_time(59) == "59min"
    assert format_time(61) == "1h1min"
