import uuid

import click
# from pathlib import Path
from feast.feature_store import FeatureStore
from .auth import AuthenticatedClient
from feature_store_api_client.api.default import post_feature_store_name
from feature_store_api_client.models import CreateFeatureStoreRequest, \
    BatchSource, BatchSourceSourceOptions, Feature, \
    Entity, FeatureView, FeatureViewTags, FeatureStore as DominoFeatureStore


@click.command()
@click.option('--name', prompt='Name of your Feature Store',
              help='Unique name for your feature store')
def domino_sync(name):
    """Sync information in registry.db with Domino"""
    # repo = Path.cwd()
    domino = AuthenticatedClient(
        base_url="https://mcetin11886.workbench-accessdata-team-sandbox.domino.tech/featurestore",
        api_key="fba753233ce044fe6264d4c96899bff83223f1b28fe251c5b5786f73123cb64d",
        token_file="",
        headers={"Accept": "application/json"},
    )


    repo = "/Users/muratcetin/github.com/real-time-credit-scoring-on-aws-tutorial/feature_repo/"
    fs = FeatureStore(repo)
    fvs = fs.list_feature_views()
    dfvs = []
    for fv in fvs:
        dfv = FeatureView(
            name=fv.name,
            ttl=fv.ttl.microseconds,
            features=[Feature(name=feature.name, dtype=str(feature.dtype)) for feature in fv.features],
            batch_source=BatchSource(
                            data_source_type=fv.batch_source.get_table_query_string(),
                            event_timestamp_column=fv.batch_source.event_timestamp_column,
                            source_options=BatchSourceSourceOptions.from_dict({
                                'query': fv.batch_source.get_table_query_string(),
                                'table_name': fv.batch_source.name,
                            }),
                            created_timestamp_column=fv.batch_source.created_timestamp_column,
            ),
            entities=[Entity(name=entity, value_type="", join_key="") for entity in fv.entities],
            tags=FeatureViewTags.from_dict(fv.tags),
        )
        dfvs.append(dfv)
    # feature_store = FS(
    #     id=uuid.UUID,
    #     project_id=uuid.UUID,
    #     feature_views=
    # )
    # fs_request = CreateFeatureStoreRequest(
    #     name=name,
    # )
    # response = post_feature_store_name.sync_detailed(
    #     name,
    #     client=domino,
    #     CreateFeatureStoreRequest(
    #         name=name,
    #         project_id="6233c82cc78b65f9181e7d45",
    #         feature_store=
    #     )
    # )
    print(f"feature views = {dfvs}")


if __name__ == '__main__':
    domino_sync()
