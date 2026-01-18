"""Trainer for Event Type Classification step."""

from __future__ import annotations

from typing import Any, Dict

from ..base_trainer import BaseTrainer
from ..config import FineTuneConfig


class EventTypeTrainer(BaseTrainer):
    """Trainer for Event Type Classification step."""
    
    def __init__(
        self,
        model_name: str,
        step_name: str = "event_type_classification",
        config: FineTuneConfig = None
    ):
        """Initialize Event Type Classification trainer.
        
        Args:
            model_name: Base model name
            step_name: Step name (default: "event_type_classification")
            config: Fine-tuning configuration (default: FineTuneConfig())
        """
        if config is None:
            config = FineTuneConfig()
        super().__init__(model_name=model_name, step_name=step_name, config=config)
