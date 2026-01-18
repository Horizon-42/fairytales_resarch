"""Trainer for Character Recognition step."""

from __future__ import annotations

from typing import Any, Dict

from ..base_trainer import BaseTrainer
from ..config import FineTuneConfig


class CharacterTrainer(BaseTrainer):
    """Trainer for Character Recognition step."""
    
    def __init__(
        self,
        model_name: str,
        step_name: str = "character_recognition",
        config: FineTuneConfig = None
    ):
        """Initialize Character Recognition trainer.
        
        Args:
            model_name: Base model name
            step_name: Step name (default: "character_recognition")
            config: Fine-tuning configuration (default: FineTuneConfig())
        """
        if config is None:
            config = FineTuneConfig()
        super().__init__(model_name=model_name, step_name=step_name, config=config)
