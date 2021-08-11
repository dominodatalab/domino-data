#!/bin/sh

set -e

# not to be committed, for aaron

cp ../domino/trainingset/web/trainingset.yaml . ## XXX for aaron's setup

openapi-python-client update --path trainingset.yaml
