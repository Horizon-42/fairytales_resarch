"""Trainer for Action Category Deduction step."""

from __future__ import annotations

from typing import Any, Dict

from ..base_trainer import BaseTrainer
from ..config import FineTuneConfig


class ActionTrainer(BaseTrainer):
    """Trainer for Action Category Deduction step."""
    
    def __init__(
        self,
        model_name: str,
        step_name: str = "action_category",
        config: FineTuneConfig = None
    ):
        """Initialize Action Category Deduction trainer.
        
        Args:
            model_name: Base model name
            step_name: Step name (default: "action_category")
            config: Fine-tuning configuration (default: FineTuneConfig())
        """
        if config is None:
            config = FineTuneConfig()
        super().__init__(model_name=model_name, step_name=step_name, config=config)
