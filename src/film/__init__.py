"""Gerchberg-Saxton film/batch tools for the standalone GDoeSII DOE Generator.

The film package deliberately supports only arbitrary-image Gerchberg-Saxton
DOEs. Analytical DOE generators remain in the normal single-DOE application.
"""

from .film_config import FilmConfig
from .film_batch import discover_frames, run_batch

__all__ = ["FilmConfig", "discover_frames", "run_batch"]
