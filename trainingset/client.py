from collections.abc import Mapping
import datetime
from enum import Enum
from typing import Optional

import openapi_client
from openapi_client.configuration import Configuration


class TrainingSetType(Enum):
    GENERIC = 1
    TRAINING = 2
    PREDICTION = 3
    GROUND_TRUTH = 4


class TrainingSet:
    def __init__(
            self,
            id: str,
            version_number: int,
            name: str,
            description: str,
            type: TrainingSetType,
            creation_time: datetime.datetime,
            owner_id: str,
            metadata: Mapping[str, str],
            annotations: Mapping[str, str],
            archived: bool
    ):
        pass


class TrainingSetClient:
    def __init__(
            self,
            configuration: Configuration,
    ):
        self.configuration = configuration

    def create_featureset(
            self,
            name: str,
            kind: TrainingSetType,
            description: Optional[str] = None,
            metadata: Mapping[str, str] = {},
            annotations: Mapping[str, str] = {}
    ) -> TrainingSet:
        """Registers a new FeatureSet"""

        with self._get_client() as api_client:
            api_instance = default_api.DefaultApi(api_client)
            api_response = api_instance.root_post(CreateTrainingSetRequest(
                name=name,
                project_id=project_id,
                description=description,
                kind=kind,
                metadata=metadata,
                annotations=annotations,
            ))

            pprint(api_response)

            return api_response

    def _get_client(self) -> openapi_client.ApiClient:
        return openapi_client.ApiClient(self.configuration)


def client() -> TrainingSetClient:
    """Get client configured from environment variables"""
    configuration = openapi_client.Configuration(
        host="http://minikube.local.domino.tech/trainingset"
    )

    return TrainingSetClient(configuration)
