"""Errors raised by the request-transform pipeline.

Every error here is a *degrade* signal, never a client-facing 4xx. I9 catches these
and lets the original request continue (contract §2, I9).
"""

from __future__ import annotations


class TransformError(Exception):
    """Base class for every transform failure that must degrade to the original."""

class CanonicalisationError(TransformError):
    """A message shape cannot be represented canonically (I2)."""

class EffectiveRequestError(TransformError):
    """An effective request could not be derived (I3)."""

class ValidationFailure(TransformError):
    """An effective request failed structural validation (I8)."""

class CapabilityLoss(TransformError):
    """A transform would drop a capability the request requires (I6)."""
