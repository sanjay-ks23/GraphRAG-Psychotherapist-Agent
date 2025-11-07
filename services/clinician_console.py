"""Clinician console service placeholder"""
from __future__ import annotations
from core.utils import get_logger

logger = get_logger(__name__)

class ClinicianConsole:
    async def list_escalations(self):
        return []

clinician_console = ClinicianConsole()
