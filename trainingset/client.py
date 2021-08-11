from collections.abc import Mapping
from typing import Optional

from training_set_api_client import Client
from training_set_api_client.api.default import post
from training_set_api_client import models as apimodels

from trainingset import models


class TrainingSetClient:
    def __init__(
            self,
    ):
        pass

    def create_featureset(
            self,
            name: str,
            project_id: str,
            kind: models.TrainingSetType,
            description: Optional[str] = None,
            metadata: Mapping[str, str] = {},
            annotations: Mapping[str, str] = {},
    ) -> models.TrainingSet:
        """Registers a new FeatureSet"""

        response = post(
            client=self._get_client(),
            json_body=apimodels.CreateTrainingSetRequest(
                name=name,
                project_id=project_id,
                kind=apimodels.CreateTrainingSetRequestKind[kind.name],
                metadata=apimodels.CreateTrainingSetRequestMetadata.from_dict(metadata),
                annotations=apimodels.CreateTrainingSetRequestAnnotations.from_dict(annotations),
                description=description,
            )
        )

        print("*** RESPONSE:")
        print(response)

    def _get_client() -> Client:
        return Client(base_url="http://minikube.local.domino.tech/trainingset")


def client() -> TrainingSetClient:
    """Get client configured from environment variables"""

    return TrainingSetClient()
