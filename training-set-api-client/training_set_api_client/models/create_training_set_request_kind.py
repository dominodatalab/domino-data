from enum import Enum


class CreateTrainingSetRequestKind(str, Enum):
    GENERIC = "Generic"
    TRAINING = "Training"
    PREDICTION = "Prediction"
    GROUNDTRUTH = "GroundTruth"

    def __str__(self) -> str:
        return str(self.value)
