"""Compatibility name for the unified experience/world model."""
from .learning import OutcomeLearner, ExperienceModel


class PredictiveModel(OutcomeLearner):
    """Backward-compatible alias; prediction and learning share one model."""
    pass
