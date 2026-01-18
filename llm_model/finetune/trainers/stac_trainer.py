"""Trainer for STAC Analysis step."""

from __future__ import annotations

from typing import Any, Dict

from ..base_trainer import BaseTrainer
from ..config import FineTuneConfig


class StacTrainer(BaseTrainer):
    """Trainer for STAC Analysis step."""
    
    def __init__(
        self,
        model_name: str,
        step_name: str = "stac_analysis",
        config: FineTuneConfig = None
    ):
        """Initialize STAC Analysis trainer.
        
        Args:
            model_name: Base model name
            step_name: Step name (default: "stac_analysis")
            config: Fine-tuning configuration (default: FineTuneConfig())
        """
        if config is None:
            config = FineTuneConfig()
        super().__init__(model_name=model_name, step_name=step_name, config=config)
