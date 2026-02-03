"""
Tests unitaires pour les fonctions utilitaires de base.
"""
import pytest
from datetime import datetime, timezone
from app.utils import get_utc_now


def test_get_utc_now():
    """Test que get_utc_now retourne bien un datetime UTC avec timezone."""
    now = get_utc_now()
    
    assert isinstance(now, datetime)
    assert now.tzinfo is not None
    assert now.tzinfo == timezone.utc


def test_get_utc_now_timezone():
    """Test que get_utc_now retourne bien UTC."""
    now = get_utc_now()
    
    # Vérifier que c'est bien UTC
    assert now.tzinfo == timezone.utc
    
    # Vérifier que l'offset est 0 (UTC)
    assert now.utcoffset().total_seconds() == 0


def test_get_utc_now_is_recent():
    """Test que get_utc_now retourne une date récente."""
    now = get_utc_now()
    expected_min = datetime.now(timezone.utc).timestamp() - 5  # 5 secondes de marge
    expected_max = datetime.now(timezone.utc).timestamp() + 5
    
    assert expected_min <= now.timestamp() <= expected_max
