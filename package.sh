#!/bin/sh

PACKAGE_FILES="spoton_elb_sync.py"


if [ -z "$1" ]; then
    echo "Usage:  $0 <version>" >&2
    exit 1
fi
VERSION=$1

set -e

rm -f spoton-${VERSION}.zip
zip spoton-${VERSION}.zip $PACKAGE_FILES

rm -f spoton-${VERSION}.json
sed "s/SPOTON_VERSION/${VERSION}/g" template.json > spoton-${VERSION}.json

ls -lh spoton-${VERSION}.*

echo "Task 1: upload spoton-${VERSION}.json to S3 -- aws s3 cp spoton-${VERSION}.json s3://pequod-public/spoton/spoton-${VERSION}.json"
echo "Task 2: upload spoton-${VERSION}.zip to S3 -- aws s3 cp spoton-${VERSION}.zip s3://pequod-public/spoton/spoton-${VERSION}.zip"
echo "Task 3: Tag git repository -- git tag $VERSION && git push --tags"
echo "Task 4: Add 'Launch Stack' button to GitHub release -- [![Launch Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home#/stacks/new?stackName=SpotOn&templateURL=https://s3-eu-central-1.amazonaws.com/pequod-public/spoton/spoton-${VERSION}.json)"
