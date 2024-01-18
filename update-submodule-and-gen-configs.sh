#!/bin/sh

make update-submodules

if ! git diff --cached --exit-code -s .gitmodules; then
    echo "Detecting changes in data-services, generating..."

    make gen-services

    if ! git diff --exit-code --name-only domino_data/configuration_gen.py; then
        echo "Please commit again."
        exit 1
    fi
fi
