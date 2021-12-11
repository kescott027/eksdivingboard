'''
# AWS Lambda Layer with kubectl (and helm)

<!--BEGIN STABILITY BANNER-->---


![cdk-constructs: Stable](https://img.shields.io/badge/cdk--constructs-stable-success.svg?style=for-the-badge)

---
<!--END STABILITY BANNER-->

This module exports a single class called `KubectlLayer` which is a `lambda.Layer` that bundles the [`kubectl`](https://kubernetes.io/docs/reference/kubectl/kubectl/) and the [`helm`](https://helm.sh/) command line.

> * Helm Version: 3.5.4
> * Kubectl Version: 1.20.0

Usage:

```python
# KubectlLayer bundles the 'kubectl' and 'helm' command lines
from aws_cdk.lambda_layer_kubectl import KubectlLayer

# fn is of type Function

fn.add_layers(KubectlLayer(self, "KubectlLayer"))
```

`kubectl` will be installed under `/opt/kubectl/kubectl`, and `helm` will be installed under `/opt/helm/helm`.
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


class KubectlLayer(
    aws_cdk.aws_lambda.LayerVersion,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk/lambda-layer-kubectl.KubectlLayer",
):
    '''An AWS Lambda layer that includes ``kubectl`` and ``helm``.

    Example::

        # KubectlLayer bundles the 'kubectl' and 'helm' command lines
        from aws_cdk.lambda_layer_kubectl import KubectlLayer
        
        # fn is of type Function
        
        fn.add_layers(KubectlLayer(self, "KubectlLayer"))
    '''

    def __init__(self, scope: constructs.Construct, id: builtins.str) -> None:
        '''
        :param scope: -
        :param id: -
        '''
        jsii.create(self.__class__, self, [scope, id])


__all__ = [
    "KubectlLayer",
]

publication.publish()
