"""Generator for Datasource Enums and Config entities."""

import argparse
import re
from collections import defaultdict
from datetime import datetime

import yaml
from jinja2 import BaseLoader, Environment, Template


"""
    Args:
        word (str): The string to be reformatted

    Returns:
        A snake case formatted version of the inputted string.
        The last letter is always lowercased.
"""
def snake_case(word: str):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", word[:-1]).lower() + word[-1].lower()


env = Environment(loader=BaseLoader())
env.filters["snake_case"] = snake_case


GenMessage = env.from_string(
    '''"""Code generated by gen.py; DO NOT EDIT.
This file was generated by robots at
{{ timestamp }}"""'''
)

Enums = env.from_string(
    '''
from enum import Enum

import attr

CREDENTIAL_TYPE = "credential"
CONFIGURATION_TYPE = "configuration"

def _cred(elem: CredElem) -> Any:
    """Type helper for credentials attributes."""
    metadata = {
        ELEMENT_TYPE_METADATA: CREDENTIAL_TYPE,
        ELEMENT_VALUE_METADATA: elem,
    }
    return attr.ib(default=None, kw_only=True, metadata=metadata)


def _config(elem: ConfigElem) -> Any:
    """Type helper for configuration attributes."""
    metadata = {
        ELEMENT_TYPE_METADATA: CONFIGURATION_TYPE,
        ELEMENT_VALUE_METADATA: elem,
    }
    return attr.ib(default=None, kw_only=True, metadata=metadata)


class ConfigElem(Enum):
    """Enumeration of valid config elements."""

    {% for value in datasource_fields -%}
    {{ value | upper }} = "{{ value }}"
    {% endfor %}

class CredElem(Enum):
    """Enumeration of valid credential elements."""

    {% for value in auth_fields -%}
    {{ value | upper }} = "{{ value }}"
    {% endfor %}
    '''
)

Configs = env.from_string(
    '''
{% for config in datasource_configs -%}
@attr.s(auto_attribs=True)
class {{ config }}(Config):
    """{{ config }} datasource configuration."""

    {% for name_map in datasource_names[config] -%}
        {{ name_map["alias"] | snake_case }}: Optional[str] = _config(elem=ConfigElem.{{ name_map["name"] | upper}})
    {% endfor %}
    {% for name_map in auth_names[config] -%}
        {{ name_map["alias"] | snake_case }}: Optional[str] = _cred(elem=CredElem.{{ name_map["name"] | upper }})
    {% endfor %}

{% endfor %}'''
)


def main(args):
    """Entrypoint for code generation."""

    with open(args.openapi, encoding="ascii") as openapi:
        schemas = yaml.load(openapi, Loader=yaml.FullLoader)["components"]["schemas"]

    with open(args.config, encoding="ascii") as config_file:
        configs = yaml.load(config_file, Loader=yaml.FullLoader)

    datasource_configs = configs["datasource_configs"]
    auth_configs = configs["auth_configs"]

    datasource_names = {}
    auth_names = {}

    for config_name, config_info in datasource_configs.items():
        entered_names = set()
        datasource_names[config_name] = []
        for field_name, field_info in config_info["fields"].items():
            if field_info["isOverridable"] and field_info["name"] not in entered_names:
                datasource_names[config_name].append(
                    {
                        "alias": field_info.get("alias", field_info["name"]),
                        "name": field_info["name"],
                    }
                )
                entered_names.add(field_info["name"])

    for config_name, config_info in datasource_configs.items():
        entered_names = set()
        auth_names[config_name] = []
        for auth_type in config_info["authTypes"]:
            for field_name, field_info in auth_configs[auth_type]["fields"].items():
                if field_info["isOverridable"] and field_info["name"] not in entered_names:
                    auth_names[config_name].append(
                        {
                            "alias": field_info.get("alias", field_info["name"]),
                            "name": field_info["name"],
                        }
                    )
                    entered_names.add(field_info["name"])

    with open(args.file, "w", encoding="ascii") as gen:
        gen.write(env.get_template(GenMessage).render(timestamp=datetime.utcnow()))
        gen.write(
            env.get_template(Enums).render(
                auth_fields=schemas["AuthFieldName"]["enum"],
                datasource_fields=schemas["DatasourceFieldName"]["enum"],
            )
        )
        gen.write(
            env.get_template(Configs).render(
                datasource_configs=configs["datasource_configs"],
                datasource_names=datasource_names,
                auth_names=auth_names,
            ),
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--openapi",
        default="services/datasource/openapi.yaml",
    )
    parser.add_argument(
        "--config",
        default="services/datasource/config.yaml",
    )
    parser.add_argument(
        "--file",
        default="domino_data/configuration_gen.py",
    )
    main(parser.parse_args())
