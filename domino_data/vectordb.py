from typing import Dict, Union

import os

HEADER_DOMINO_DATASOURCE = "X-Domino-Datasource"
HEADER_PINECONE_INDEX = "X-Domino-Pinecone-Index"


def domino_pinecone3x_init_params(datasource_name: str) -> Dict[str, Union[str, Dict[str, str]]]:
    """Wrap the parameters to initialize a Pinecone 3.x and above client

    Args:
        datasource_name: the name of the Pinecone data source

    Returns:
        A dictionary of parameters to initialize the Pinecone client
    """
    return {
        "api_key": "domino",
        "host": os.getenv("DOMINO_DATA_API_GATEWAY", "http://127.0.0.1:8766"),
        "additional_headers": {HEADER_DOMINO_DATASOURCE: datasource_name},
    }


def domino_pinecone3x_index_params(
    datasource_name: str, index_name: str
) -> Dict[str, Union[str, Dict[str, str]]]:
    """Wrap the parameters to target an index in the Pinecone 3.x and above client

    Args:
        datasource_name: the name of the Pinecone data source
        index_name: the name of the index

    Returns:
        A dictionary of parameters to target the Pinecone index for vector operations
    """
    return {
        "host": os.getenv("DOMINO_DATA_API_GATEWAY", "http://127.0.0.1:8766"),
        "additional_headers": {
            HEADER_DOMINO_DATASOURCE: datasource_name,
            HEADER_PINECONE_INDEX: index_name,
        },
    }
