'''
# AWS Lambda Layer with AWS CLI

<!--BEGIN STABILITY BANNER-->---


![cdk-constructs: Stable](https://img.shields.io/badge/cdk--constructs-stable-success.svg?style=for-the-badge)

---
<!--END STABILITY BANNER-->

This module exports a single class called `AwsCliLayer` which is a `lambda.Layer` that bundles the AWS CLI.

Usage:

```python
# AwsCliLayer bundles the AWS CLI in a lambda layer
from aws_cdk.lambda_layer_awscli import AwsCliLayer

# fn is of type Function

fn.add_layers(AwsCliLayer(self, "AwsCliLayer"))
```

The CLI will be installed under `/opt/awscli/aws`.
'''
import abc
import builtins
import datetime
import enum
import typing

import jsii
import publication
import typing_extensions

from ._jsii import *

import aws_cdk.aws_lambda
import constructs


class AwsCliLayer(
    aws_cdk.aws_lambda.LayerVersion,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk/lambda-layer-awscli.AwsCliLayer",
):
    '''An AWS Lambda layer that includes the AWS CLI.

    Example::

        # AwsCliLayer bundles the AWS CLI in a lambda layer
        from aws_cdk.lambda_layer_awscli import AwsCliLayer
        
        # fn is of type Function
        
        fn.add_layers(AwsCliLayer(self, "AwsCliLayer"))
    '''

    def __init__(self, scope: constructs.Construct, id: builtins.str) -> None:
        '''
        :param scope: -
        :param id: -
        '''
        jsii.create(self.__class__, self, [scope, id])


__all__ = [
    "AwsCliLayer",
]

publication.publish()
