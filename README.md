<img src="spotlight.png" align="right" height="90"/>
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

Installing Spot On! in your account provides you the glue that makes Spot Fleet easily usable for
your microservices.

## How to install Spot On!?

For the installation, Spot On! provides a simple
[CloudFormation](https://aws.amazon.com/cloudformation/) template that you only need to instantiate
once in your AWS account.

Go to the [Release page](https://github.com/zalando/spoton/releases) and use the "Launch Stack"
buttons for your prefered version.

[![Launch Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://github.com/zalando/spoton/releases)

## How to use Spot On!?

Spot On! is a collection of [AWS Lambda](https://aws.amazon.com/lambda/) functions that provide the
glue between the necessary services. These are running in the background of your AWS account and
will connect your services on-demand.

### AWS Elastic Load Balancing

SpotOn will register all spot instances of your Spot Fleet requests in the ELBs that link via
[AWS Tags](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Using_Tags.html) to the request. The
general concept is as follows:

* **Step 1:** Create a Spot Fleet Request and use its ID in the next step.
* **Step 2:** Create an ElasticLoadBalancer and give it the tag `SpotFleetRequestId =
  sfr-e2b3ce89-2441-4bdc-8d0d-b2828a1da8b7` (the ID of the step before).

Spot On! can now automatically connect the dots and knows that instances from your Spot Fleet
should be registered in your ELB. Your instances will now appear and disappear in the ELBs instance
list.

### AWS CloudWatch (Auto Scaling)

Not implemented yet.

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
