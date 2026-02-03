"""
Optimisations Python 3.13 pour ChronoTrak
Version simplifiée - optimisations automatiques via variables d'environnement
"""

import os
import sys
from typing import Any

# Vérification de la version Python
PYTHON_313_AVAILABLE = sys.version_info >= (3, 13)


def get_python313_info() -> dict[str, Any]:
    """Retourne les informations sur les optimisations Python 3.13"""

    return {
        "python_version": sys.version,
        "python_313_available": PYTHON_313_AVAILABLE,
        "jit_enabled": os.environ.get("PYTHON_JIT") == "1",
        "optimizations_enabled": os.environ.get("PYTHONOPTIMIZE") == "1",
        "memory_allocator": os.environ.get("PYTHONMALLOC", "default"),
    }


# Les optimisations sont automatiques via les variables d'environnement
# définies dans le Dockerfile (production) et config.py (développement)
