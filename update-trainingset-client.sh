#!/bin/sh

set -e

# not to be committed, for aaron

cp ../domino/trainingset/web/trainingset.yaml ./trainingset ## XXX for aaron's setup

staging=$(mktemp -d)
openapi-generator generate -i trainingset/trainingset.yaml -g python -o $staging

rm -rf trainingset/openapi_client
mv $staging/openapi_client trainingset

rm -rf $staging
