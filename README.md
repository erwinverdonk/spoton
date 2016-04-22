# Spot On!

This project helps you to use
[AWS Spot Fleet](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-fleet.html) for
stateless services. Why we need an extra project for that? Because Spot Fleet has no integration
points with any of the important EC2 services!

The classical set up for stateless services is pretty simple: Use an
[AWS AutoScalingGroup](https://aws.amazon.com/autoscaling/) to manage the number of instances you
need and automatically connect them with your
[AWS ElasticLoadBalancer](https://aws.amazon.com/elasticloadbalancing/). Spot Fleet can neither
manage your ELB enlistement nor does it integrate with
[AWS CloudWatch](https://aws.amazon.com/cloudwatch/) to provide automatic up and down scaling of
your instances.

## How to use SpotOn?

SpotOn is a collection of [AWS Lambda](https://aws.amazon.com/lambda/) functions that provide the
glue between the necessary services. For the installation, SpotOn provides a simple installation
script that you only need to use once to install SpotOn in your AWS account.

SpotOn will enlist all spot instances of your Spot Fleet requests in the ELBs that link via
[AWS Tags](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Using_Tags.html) to the request. The
general concept is as follows:

* **Step 0:** (only required once) Install SpotOn via the `install.sh` script.
* **Step 2:** Create a Spot Fleet Request and use its ID in the next step.
* **Step 1:** Create an ELB and give it the tag `SpotFleetRequestId =
  sfr-e2b3ce89-2441-4bdc-8d0d-b2828a1da8b7` (the ID of the step before).

SpotOn can now connect the dots and knows that instances from your Spot Fleet should be connected
with your ELB. Your instances will now automatically appear and disappear in the ELBs instance
list.

## How does it work?

SpotOn consists of multiple Lambda functions:

### spoton-elb-sync

The SpotOn ELB sync function constantly keeps the ELB instance lists up-to-date. This function runs
every minute. Its job looks like that:

* Get a list of all (active) Spot Fleet Requests.
  * If no requests exists, abort execution - SpotOn isn't required.
* Get a list of all ElasticLoadBalancers and fetch the tags for each of them.
  * If no ELB exists with a `SpotFleetRequestId`, abort execution - Spot is only used for other
    things.
* For each Spot Fleet Request where a corresponding ELB exists:
  * Fetch the list of all instances of the Spot Fleet Request and fetch the tags for each of them.
  * Compare list of instances of the Spot Fleet Request with the list of instances of the ELB:
    * Add all instances of the Spot Fleet Request that are *eligible* and missing.
    * Remove all other instances from the ELB.

*Eligible* are all instances that have no tag `SpotFleetELB = ignore`. This can be used if you want
to prevent temporarily dead instances in your ELB pool. Without this feature, if your instance
terminates, the ELB will forward requests to the dead instance until the health check recognizes
its death. This might lead to a couple of failed requests. To prevent that, Spot Instances have the
possibility to figure out for them self, if they get terminated soon via the [termincation
notification](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-interruptions.html#spot-instance-termination-notices).
You can instrument your instances (AMIs) to regularly check for the instance termination
notification and add the tag `SpotFleetELB = ignore` as soon as termination is detected. This will
tell SpotOn to remove the instance from the ELB even if the instance is not dead yet.

CloudWatch Events could have been used as a reactive approach but it comes with a couple of corner
cases. One big problem is that Spot Requests need to exist before you can tag the ELB with the
Request ID (that you just don't know in advance). This leads to the situation that you already have
instances running before the tag is active. These wouldn't trigger further events and so those
wouldn't get listed. To compensate that, you would need to sync the whole list of instances on any
event but there is no guarentee that even one trigger happens in the next time. This brings us back
to simple, regular syncs which are much more reliable and self-healing in case of problems.

### spoton-autoscaling

The SpotOn auto scaling function will increase or decrease the capacity configuration of your
Spot Fleet Request according to the average metrics of its instances. This function runs every
minute. Its job looks like that:

* Get a list of all (active) Spot Fleet Requests.
  * If no requests exists, abort execution - SpotOn isn't required.
* Get a list of all ElasticLoadBalancers and fetch the tags for each of them.
  * If no ELB exists with a `SpotFleetRequestId`, abort execution - Spot is only used for other
    things.
* For each Spot Fleet Request where a corresponding ELB exists:
  * If the ELB has neither a `SpotFleetScaleUp` nor `SpotFleetScaleDown` tag, skip it.
  * If the timestamp of the `SpotFleetScaleTime` tag is after now, skip it (we are on cooldown for
    scaling decisions).
  * Use the `SpotFleetScaleMetric` tag's value to determine the CloudWatch metric to use for
    scaling decisions and fetch its current average value of the last minute for the Spot Fleet
    Request.
  * Compare the metric's average with the `SpotFleetScaleUp` and `SpotFleetScaleDown` values
    and increase or decrease the Spot Fleet Request's capacity by `SpotFleetScaleSteps` but only up
    to `SpotFleetScaleMinimum` or `SpotFleetScaleMaximum` if given.
  * Set `SpotFleetScaleTime` to `now() + SpotFleetScaleCooldownMinutes` to prevent too fast scaling
    decisions (scaling up or down normally takes longer than the 1 minute until this function gets
    called again).

CloudWatch Alarms could have been used as a reactive approach but it has some limitations for
good scaling decisions. Alarms only fire once for the state change `ok->alarm` or `alarm->ok`.
Imagining an alarm that triggers on 70% CPU usage, that could be used to trigger an upscale of the
Spot Fleet Request. But, if the Spot Fleet Request now finally spawned another instance, the
average CPU usage might still be over 70% because of so much load. Now the alarm wouldn't tigger
again and no upscaling would happen.

## License

The MIT License (MIT) Copyright © 2016 Zalando SE, https://tech.zalando.com

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the “Software”), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT
OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
