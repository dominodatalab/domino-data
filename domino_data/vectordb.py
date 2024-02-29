import os

_import_error_message = (
    "pinecone-client is not installed.\n\n"
    "Please pip install pinecone-client:\n\n"
    "  python -m pip install pinecone-client   # install directly\n"
)

try:
    from pinecone.core.client.configuration import Configuration as OpenApiConfiguration
except ImportError as e:
    if e.msg == "No module named 'pinecone'":
        raise ImportError(_import_error_message) from e
    else:
        raise

DOMINO_DATA_API_GATEWAY = os.getenv("DOMINO_DATA_API_GATEWAY", "http://127.0.0.1:8766")
HEADER_DOMINO_DATASOURCE = "X-Domino-Datasource"
HEADER_PINECONE_INDEX = "X-Domino-Pinecone-Index"


class DominoPineconeConfiguration(OpenApiConfiguration):
    def __init__(
        self,
        datasource=None,
        host=None,
        api_key=None,
        api_key_prefix=None,
        access_token=None,
        username=None,
        password=None,
        discard_unknown_keys=False,
        disabled_client_side_validations="",
        server_index=None,
        server_variables=None,
        server_operation_index=None,
        server_operation_variables=None,
        ssl_ca_cert=None,
    ):

        super().__init__(
            host,
            api_key,
            api_key_prefix,
            access_token,
            username,
            password,
            discard_unknown_keys,
            disabled_client_side_validations,
            server_index,
            server_variables,
            server_operation_index,
            server_operation_variables,
            ssl_ca_cert,
        )

        self.proxy = DOMINO_DATA_API_GATEWAY
        self.proxy_headers = {HEADER_DOMINO_DATASOURCE: datasource}

    def get_host_from_settings(self, index, variables=None, servers=None):
        url = super().get_host_from_settings(index, variables, servers)
        return url.replace("https://", "http://")


def domino_pinecone3x_init_params(datasource_name: str) -> dict[str, str]:
    return {
        "api_key": "domino",
        "host": DOMINO_DATA_API_GATEWAY,
        "additional_headers": {HEADER_DOMINO_DATASOURCE: datasource_name},
    }


def domino_pinecone3x_index_params(datasource_name: str, index_name: str) -> dict[str, str]:
    return {
        "host": DOMINO_DATA_API_GATEWAY,
        "additional_headers": {
            HEADER_DOMINO_DATASOURCE: datasource_name,
            HEADER_PINECONE_INDEX: index_name,
        },
    }
