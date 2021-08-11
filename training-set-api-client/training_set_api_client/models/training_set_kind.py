from enum import Enum


class TrainingSetKind(str, Enum):
    GENERIC = "Generic"
    TRAINING = "Training"
    PREDICTION = "Prediction"
    GROUNDTRUTH = "GroundTruth"

    def __str__(self) -> str:
        return str(self.value)
