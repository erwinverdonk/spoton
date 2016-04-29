#!/bin/sh

PACKAGE_FILES="spoton_elb_sync.py spoton_auto_scale.py scm-source.json"


if [ -z "$1" ]; then
    echo "Usage:  $0 <version>" >&2
    exit 1
fi
VERSION=$1

set -e

rm -f scm-source.json
scm-source

rm -f spoton-${VERSION}.zip
zip spoton-${VERSION}.zip $PACKAGE_FILES

rm -f spoton-${VERSION}.json
sed "s/SPOTON_VERSION/${VERSION}/g" template.json > spoton-${VERSION}.json

ls -lh spoton-${VERSION}.*

echo "Task 1: upload spoton-${VERSION}.json to S3 -- aws s3 cp spoton-${VERSION}.json s3://pequod-public/spoton/spoton-${VERSION}.json"
echo "Task 2: upload spoton-${VERSION}.zip to S3 -- aws s3 cp spoton-${VERSION}.zip s3://pequod-public/spoton/spoton-${VERSION}.zip"
echo "Task 3: Tag git repository -- git tag $VERSION && git push --tags"
echo "Task 4: create GitHub release with body:
---

Quickstart with Spot On! version ${VERSION}:

[![Launch Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home#/stacks/new?stackName=SpotOn&templateURL=https://s3-eu-central-1.amazonaws.com/pequod-public/spoton/spoton-${VERSION}.json)

Alternatively, to install or update, use the following CloudFormation template from S3:

    https://s3-eu-central-1.amazonaws.com/pequod-public/spoton/spoton-${VERSION}.json

## Changes

* ...
"
