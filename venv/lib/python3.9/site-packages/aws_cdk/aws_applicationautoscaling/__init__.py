'''
# AWS Auto Scaling Construct Library

<!--BEGIN STABILITY BANNER-->---


![cfn-resources: Stable](https://img.shields.io/badge/cfn--resources-stable-success.svg?style=for-the-badge)

![cdk-constructs: Stable](https://img.shields.io/badge/cdk--constructs-stable-success.svg?style=for-the-badge)

---
<!--END STABILITY BANNER-->

**Application AutoScaling** is used to configure autoscaling for all
services other than scaling EC2 instances. For example, you will use this to
scale ECS tasks, DynamoDB capacity, Spot Fleet sizes, Comprehend document classification endpoints, Lambda function provisioned concurrency and more.

As a CDK user, you will probably not have to interact with this library
directly; instead, it will be used by other construct libraries to
offer AutoScaling features for their own constructs.

This document will describe the general autoscaling features and concepts;
your particular service may offer only a subset of these.

## AutoScaling basics

Resources can offer one or more **attributes** to autoscale, typically
representing some capacity dimension of the underlying service. For example,
a DynamoDB Table offers autoscaling of the read and write capacity of the
table proper and its Global Secondary Indexes, an ECS Service offers
autoscaling of its task count, an RDS Aurora cluster offers scaling of its
replica count, and so on.

When you enable autoscaling for an attribute, you specify a minimum and a
maximum value for the capacity. AutoScaling policies that respond to metrics
will never go higher or lower than the indicated capacity (but scheduled
scaling actions might, see below).

There are three ways to scale your capacity:

* **In response to a metric** (also known as step scaling); for example, you
  might want to scale out if the CPU usage across your cluster starts to rise,
  and scale in when it drops again.
* **By trying to keep a certain metric around a given value** (also known as
  target tracking scaling); you might want to automatically scale out an in to
  keep your CPU usage around 50%.
* **On a schedule**; you might want to organize your scaling around traffic
  flows you expect, by scaling out in the morning and scaling in in the
  evening.

The general pattern of autoscaling will look like this:

```python
# resource is of type SomeScalableResource


capacity = resource.auto_scale_capacity(
    min_capacity=5,
    max_capacity=100
)
```

## Step Scaling

This type of scaling scales in and out in deterministic steps that you
configure, in response to metric values. For example, your scaling strategy
to scale in response to CPU usage might look like this:

```plaintext
 Scaling        -1          (no change)          +1       +3
            │        │                       │        │        │
            ├────────┼───────────────────────┼────────┼────────┤
            │        │                       │        │        │
CPU usage   0%      10%                     50%       70%     100%
```

(Note that this is not necessarily a recommended scaling strategy, but it's
a possible one. You will have to determine what thresholds are right for you).

You would configure it like this:

```python
# capacity is of type ScalableAttribute
# cpu_utilization is of type Metric


capacity.scale_on_metric("ScaleToCPU",
    metric=cpu_utilization,
    scaling_steps=[appscaling.ScalingInterval(upper=10, change=-1), appscaling.ScalingInterval(lower=50, change=+1), appscaling.ScalingInterval(lower=70, change=+3)
    ],

    # Change this to AdjustmentType.PercentChangeInCapacity to interpret the
    # 'change' numbers before as percentages instead of capacity counts.
    adjustment_type=appscaling.AdjustmentType.CHANGE_IN_CAPACITY
)
```

The AutoScaling construct library will create the required CloudWatch alarms and
AutoScaling policies for you.

## Target Tracking Scaling

This type of scaling scales in and out in order to keep a metric (typically
representing utilization) around a value you prefer. This type of scaling is
typically heavily service-dependent in what metric you can use, and so
different services will have different methods here to set up target tracking
scaling.

The following example configures the read capacity of a DynamoDB table
to be around 60% utilization:

```python
import aws_cdk.aws_dynamodb as dynamodb

# table is of type Table


read_capacity = table.auto_scale_read_capacity(
    min_capacity=10,
    max_capacity=1000
)
read_capacity.scale_on_utilization(
    target_utilization_percent=60
)
```

## Scheduled Scaling

This type of scaling is used to change capacities based on time. It works
by changing the `minCapacity` and `maxCapacity` of the attribute, and so
can be used for two purposes:

* Scale in and out on a schedule by setting the `minCapacity` high or
  the `maxCapacity` low.
* Still allow the regular scaling actions to do their job, but restrict
  the range they can scale over (by setting both `minCapacity` and
  `maxCapacity` but changing their range over time).

The following schedule expressions can be used:

* `at(yyyy-mm-ddThh:mm:ss)` -- scale at a particular moment in time
* `rate(value unit)` -- scale every minute/hour/day
* `cron(mm hh dd mm dow)` -- scale on arbitrary schedules

Of these, the cron expression is the most useful but also the most
complicated. A schedule is expressed as a cron expression. The `Schedule` class has a `cron` method to help build cron expressions.

The following example scales the fleet out in the morning, and lets natural
scaling take over at night:

```python
# resource is of type SomeScalableResource


capacity = resource.auto_scale_capacity(
    min_capacity=1,
    max_capacity=50
)

capacity.scale_on_schedule("PrescaleInTheMorning",
    schedule=appscaling.Schedule.cron(hour="8", minute="0"),
    min_capacity=20
)

capacity.scale_on_schedule("AllowDownscalingAtNight",
    schedule=appscaling.Schedule.cron(hour="20", minute="0"),
    min_capacity=1
)
```

## Examples

### Lambda Provisioned Concurrency Auto Scaling

```python
import aws_cdk.aws_lambda as lambda_

# code is of type Code


handler = lambda_.Function(self, "MyFunction",
    runtime=lambda_.Runtime.PYTHON_3_7,
    handler="index.handler",
    code=code,

    reserved_concurrent_executions=2
)

fn_ver = handler.add_version("CDKLambdaVersion", undefined, "demo alias", 10)

target = appscaling.ScalableTarget(self, "ScalableTarget",
    service_namespace=appscaling.ServiceNamespace.LAMBDA,
    max_capacity=100,
    min_capacity=10,
    resource_id=f"function:{handler.functionName}:{fnVer.version}",
    scalable_dimension="lambda:function:ProvisionedConcurrency"
)

target.scale_to_track_metric("PceTracking",
    target_value=0.9,
    predefined_metric=appscaling.PredefinedMetric.LAMBDA_PROVISIONED_CONCURRENCY_UTILIZATION
)
```
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

import aws_cdk.aws_cloudwatch
import aws_cdk.aws_iam
import aws_cdk.core
import constructs


@jsii.data_type(
    jsii_type="@aws-cdk/aws-applicationautoscaling.AdjustmentTier",
    jsii_struct_bases=[],
    name_mapping={
        "adjustment": "adjustment",
        "lower_bound": "lowerBound",
        "upper_bound": "upperBound",
    },
)
class AdjustmentTier:
    def __init__(
        self,
        *,
        adjustment: jsii.Number,
        lower_bound: typing.Optional[jsii.Number] = None,
        upper_bound: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''An adjustment.

        :param adjustment: What number to adjust the capacity with. The number is interpeted as an added capacity, a new fixed capacity or an added percentage depending on the AdjustmentType value of the StepScalingPolicy. Can be positive or negative.
        :param lower_bound: Lower bound where this scaling tier applies. The scaling tier applies if the difference between the metric value and its alarm threshold is higher than this value. Default: -Infinity if this is the first tier, otherwise the upperBound of the previous tier
        :param upper_bound: Upper bound where this scaling tier applies. The scaling tier applies if the difference between the metric value and its alarm threshold is lower than this value. Default: +Infinity

        Example::

            # The code below shows an example of how to instantiate this type.
            # The values are placeholders you should change.
            import aws_cdk.aws_applicationautoscaling as appscaling
            
            adjustment_tier = appscaling.AdjustmentTier(
                adjustment=123,
            
                # the properties below are optional
                lower_bound=123,
                upper_bound=123
            )
        '''
        self._values: typing.Dict[str, typing.Any] = {
            "adjustment": adjustment,
        }
        if lower_bound is not None:
            self._values["lower_bound"] = lower_bound
        if upper_bound is not None:
            self._values["upper_bound"] = upper_bound

    @builtins.property
    def adjustment(self) -> jsii.Number:
        '''What number to adjust the capacity with.

        The number is interpeted as an added capacity, a new fixed capacity or an
        added percentage depending on the AdjustmentType value of the
        StepScalingPolicy.

        Can be positive or negative.
        '''
        result = self._values.get("adjustment")
        assert result is not None, "Required property 'adjustment' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def lower_bound(self) -> typing.Optional[jsii.Number]:
        '''Lower bound where this scaling tier applies.

        The scaling tier applies if the difference between the metric
        value and its alarm threshold is higher than this value.

        :default: -Infinity if this is the first tier, otherwise the upperBound of the previous tier
        '''
        result = self._values.get("lower_bound")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def upper_bound(self) -> typing.Optional[jsii.Number]:
        '''Upper bound where this scaling tier applies.

        The scaling tier applies if the difference between the metric
        value and its alarm threshold is lower than this value.

        :default: +Infinity
        '''
        result = self._values.get("upper_bound")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AdjustmentTier(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.enum(jsii_type="@aws-cdk/aws-applicationautoscaling.AdjustmentType")
class AdjustmentType(enum.Enum):
    '''How adjustment numbers are interpreted.

    Example::

        # capacity is of type ScalableAttribute
        # cpu_utilization is of type Metric
        
        
        capacity.scale_on_metric("ScaleToCPU",
            metric=cpu_utilization,
            scaling_steps=[appscaling.ScalingInterval(upper=10, change=-1), appscaling.ScalingInterval(lower=50, change=+1), appscaling.ScalingInterval(lower=70, change=+3)
            ],
        
            # Change this to AdjustmentType.PercentChangeInCapacity to interpret the
            # 'change' numbers before as percentages instead of capacity counts.
            adjustment_type=appscaling.AdjustmentType.CHANGE_IN_CAPACITY
        )
    '''

    CHANGE_IN_CAPACITY = "CHANGE_IN_CAPACITY"
    '''Add the adjustment number to the current capacity.

    A positive number increases capacity, a negative number decreases capacity.
    '''
    EXACT_CAPACITY = "EXACT_CAPACITY"
    '''Make the capacity equal to the exact number given.'''
    PERCENT_CHANGE_IN_CAPACITY = "PERCENT_CHANGE_IN_CAPACITY"
    '''Add this percentage of the current capacity to itself.

    The number must be between -100 and 100; a positive number increases
    capacity and a negative number decreases it.
    '''


class BaseScalableAttribute(
    aws_cdk.core.Construct,
    metaclass=jsii.JSIIAbstractClass,
    jsii_type="@aws-cdk/aws-applicationautoscaling.BaseScalableAttribute",
):
    '''Represent an attribute for which autoscaling can be configured.

    This class is basically a light wrapper around ScalableTarget, but with
    all methods protected instead of public so they can be selectively
    exposed and/or more specific versions of them can be exposed by derived
    classes for individual services support autoscaling.

    Typical use cases:

    - Hide away the PredefinedMetric enum for target tracking policies.
    - Don't expose all scaling methods (for example Dynamo tables don't support
      Step Scaling, so the Dynamo subclass won't expose this method).
    '''

    def __init__(
        self,
        scope: constructs.Construct,
        id: builtins.str,
        *,
        dimension: builtins.str,
        resource_id: builtins.str,
        role: aws_cdk.aws_iam.IRole,
        service_namespace: "ServiceNamespace",
        max_capacity: jsii.Number,
        min_capacity: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param dimension: Scalable dimension of the attribute.
        :param resource_id: Resource ID of the attribute.
        :param role: Role to use for scaling.
        :param service_namespace: Service namespace of the scalable attribute.
        :param max_capacity: Maximum capacity to scale to.
        :param min_capacity: Minimum capacity to scale to. Default: 1
        '''
        props = BaseScalableAttributeProps(
            dimension=dimension,
            resource_id=resource_id,
            role=role,
            service_namespace=service_namespace,
            max_capacity=max_capacity,
            min_capacity=min_capacity,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="doScaleOnMetric")
    def _do_scale_on_metric(
        self,
        id: builtins.str,
        *,
        adjustment_type: typing.Optional[AdjustmentType] = None,
        cooldown: typing.Optional[aws_cdk.core.Duration] = None,
        evaluation_periods: typing.Optional[jsii.Number] = None,
        metric: aws_cdk.aws_cloudwatch.IMetric,
        metric_aggregation_type: typing.Optional["MetricAggregationType"] = None,
        min_adjustment_magnitude: typing.Optional[jsii.Number] = None,
        scaling_steps: typing.Sequence["ScalingInterval"],
    ) -> None:
        '''Scale out or in based on a metric value.

        :param id: -
        :param adjustment_type: How the adjustment numbers inside 'intervals' are interpreted. Default: ChangeInCapacity
        :param cooldown: Grace period after scaling activity. Subsequent scale outs during the cooldown period are squashed so that only the biggest scale out happens. Subsequent scale ins during the cooldown period are ignored. Default: No cooldown period
        :param evaluation_periods: How many evaluation periods of the metric to wait before triggering a scaling action. Raising this value can be used to smooth out the metric, at the expense of slower response times. Default: 1
        :param metric: Metric to scale on.
        :param metric_aggregation_type: Aggregation to apply to all data points over the evaluation periods. Only has meaning if ``evaluationPeriods != 1``. Default: - The statistic from the metric if applicable (MIN, MAX, AVERAGE), otherwise AVERAGE.
        :param min_adjustment_magnitude: Minimum absolute number to adjust capacity with as result of percentage scaling. Only when using AdjustmentType = PercentChangeInCapacity, this number controls the minimum absolute effect size. Default: No minimum scaling effect
        :param scaling_steps: The intervals for scaling. Maps a range of metric values to a particular scaling behavior.
        '''
        props = BasicStepScalingPolicyProps(
            adjustment_type=adjustment_type,
            cooldown=cooldown,
            evaluation_periods=evaluation_periods,
            metric=metric,
            metric_aggregation_type=metric_aggregation_type,
            min_adjustment_magnitude=min_adjustment_magnitude,
            scaling_steps=scaling_steps,
        )

        return typing.cast(None, jsii.invoke(self, "doScaleOnMetric", [id, props]))

    @jsii.member(jsii_name="doScaleOnSchedule")
    def _do_scale_on_schedule(
        self,
        id: builtins.str,
        *,
        end_time: typing.Optional[datetime.datetime] = None,
        max_capacity: typing.Optional[jsii.Number] = None,
        min_capacity: typing.Optional[jsii.Number] = None,
        schedule: "Schedule",
        start_time: typing.Optional[datetime.datetime] = None,
    ) -> None:
        '''Scale out or in based on time.

        :param id: -
        :param end_time: When this scheduled action expires. Default: The rule never expires.
        :param max_capacity: The new maximum capacity. During the scheduled time, the current capacity is above the maximum capacity, Application Auto Scaling scales in to the maximum capacity. At least one of maxCapacity and minCapacity must be supplied. Default: No new maximum capacity
        :param min_capacity: The new minimum capacity. During the scheduled time, if the current capacity is below the minimum capacity, Application Auto Scaling scales out to the minimum capacity. At least one of maxCapacity and minCapacity must be supplied. Default: No new minimum capacity
        :param schedule: When to perform this action.
        :param start_time: When this scheduled action becomes active. Default: The rule is activate immediately
        '''
        props = ScalingSchedule(
            end_time=end_time,
            max_capacity=max_capacity,
            min_capacity=min_capacity,
            schedule=schedule,
            start_time=start_time,
        )

        return typing.cast(None, jsii.invoke(self, "doScaleOnSchedule", [id, props]))

    @jsii.member(jsii_name="doScaleToTrackMetric")
    def _do_scale_to_track_metric(
        self,
        id: builtins.str,
        *,
        custom_metric: typing.Optional[aws_cdk.aws_cloudwatch.IMetric] = None,
        predefined_metric: typing.Optional["PredefinedMetric"] = None,
        resource_label: typing.Optional[builtins.str] = None,
        target_value: jsii.Number,
        disable_scale_in: typing.Optional[builtins.bool] = None,
        policy_name: typing.Optional[builtins.str] = None,
        scale_in_cooldown: typing.Optional[aws_cdk.core.Duration] = None,
        scale_out_cooldown: typing.Optional[aws_cdk.core.Duration] = None,
    ) -> None:
        '''Scale out or in in order to keep a metric around a target value.

        :param id: -
        :param custom_metric: A custom metric for application autoscaling. The metric must track utilization. Scaling out will happen if the metric is higher than the target value, scaling in will happen in the metric is lower than the target value. Exactly one of customMetric or predefinedMetric must be specified. Default: - No custom metric.
        :param predefined_metric: A predefined metric for application autoscaling. The metric must track utilization. Scaling out will happen if the metric is higher than the target value, scaling in will happen in the metric is lower than the target value. Exactly one of customMetric or predefinedMetric must be specified. Default: - No predefined metrics.
        :param resource_label: Identify the resource associated with the metric type. Only used for predefined metric ALBRequestCountPerTarget. Example value: ``app/<load-balancer-name>/<load-balancer-id>/targetgroup/<target-group-name>/<target-group-id>`` Default: - No resource label.
        :param target_value: The target value for the metric.
        :param disable_scale_in: Indicates whether scale in by the target tracking policy is disabled. If the value is true, scale in is disabled and the target tracking policy won't remove capacity from the scalable resource. Otherwise, scale in is enabled and the target tracking policy can remove capacity from the scalable resource. Default: false
        :param policy_name: A name for the scaling policy. Default: - Automatically generated name.
        :param scale_in_cooldown: Period after a scale in activity completes before another scale in activity can start. Default: Duration.seconds(300) for the following scalable targets: ECS services, Spot Fleet requests, EMR clusters, AppStream 2.0 fleets, Aurora DB clusters, Amazon SageMaker endpoint variants, Custom resources. For all other scalable targets, the default value is Duration.seconds(0): DynamoDB tables, DynamoDB global secondary indexes, Amazon Comprehend document classification endpoints, Lambda provisioned concurrency
        :param scale_out_cooldown: Period after a scale out activity completes before another scale out activity can start. Default: Duration.seconds(300) for the following scalable targets: ECS services, Spot Fleet requests, EMR clusters, AppStream 2.0 fleets, Aurora DB clusters, Amazon SageMaker endpoint variants, Custom resources. For all other scalable targets, the default value is Duration.seconds(0): DynamoDB tables, DynamoDB global secondary indexes, Amazon Comprehend document classification endpoints, Lambda provisioned concurrency
        '''
        props = BasicTargetTrackingScalingPolicyProps(
            custom_metric=custom_metric,
            predefined_metric=predefined_metric,
            resource_label=resource_label,
            target_value=target_value,
            disable_scale_in=disable_scale_in,
            policy_name=policy_name,
            scale_in_cooldown=scale_in_cooldown,
            scale_out_cooldown=scale_out_cooldown,
        )

        return typing.cast(None, jsii.invoke(self, "doScaleToTrackMetric", [id, props]))

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="props")
    def _props(self) -> "BaseScalableAttributeProps":
        return typing.cast("BaseScalableAttributeProps", jsii.get(self, "props"))


class _BaseScalableAttributeProxy(BaseScalableAttribute):
    pass

# Adding a "__jsii_proxy_class__(): typing.Type" function to the abstract class
typing.cast(typing.Any, BaseScalableAttribute).__jsii_proxy_class__ = lambda : _BaseScalableAttributeProxy


@jsii.data_type(
    jsii_type="@aws-cdk/aws-applicationautoscaling.BaseTargetTrackingProps",
    jsii_struct_bases=[],
    name_mapping={
        "disable_scale_in": "disableScaleIn",
        "policy_name": "policyName",
        "scale_in_cooldown": "scaleInCooldown",
        "scale_out_cooldown": "scaleOutCooldown",
    },
)
class BaseTargetTrackingProps:
    def __init__(
        self,
        *,
        disable_scale_in: typing.Optional[builtins.bool] = None,
        policy_name: typing.Optional[builtins.str] = None,
        scale_in_cooldown: typing.Optional[aws_cdk.core.Duration] = None,
        scale_out_cooldown: typing.Optional[aws_cdk.core.Duration] = None,
    ) -> None:
        '''Base interface for target tracking props.

        Contains the attributes that are common to target tracking policies,
        except the ones relating to the metric and to the scalable target.

        This interface is reused by more specific target tracking props objects
        in other services.

        :param disable_scale_in: Indicates whether scale in by the target tracking policy is disabled. If the value is true, scale in is disabled and the target tracking policy won't remove capacity from the scalable resource. Otherwise, scale in is enabled and the target tracking policy can remove capacity from the scalable resource. Default: false
        :param policy_name: A name for the scaling policy. Default: - Automatically generated name.
        :param scale_in_cooldown: Period after a scale in activity completes before another scale in activity can start. Default: Duration.seconds(300) for the following scalable targets: ECS services, Spot Fleet requests, EMR clusters, AppStream 2.0 fleets, Aurora DB clusters, Amazon SageMaker endpoint variants, Custom resources. For all other scalable targets, the default value is Duration.seconds(0): DynamoDB tables, DynamoDB global secondary indexes, Amazon Comprehend document classification endpoints, Lambda provisioned concurrency
        :param scale_out_cooldown: Period after a scale out activity completes before another scale out activity can start. Default: Duration.seconds(300) for the following scalable targets: ECS services, Spot Fleet requests, EMR clusters, AppStream 2.0 fleets, Aurora DB clusters, Amazon SageMaker endpoint variants, Custom resources. For all other scalable targets, the default value is Duration.seconds(0): DynamoDB tables, DynamoDB global secondary indexes, Amazon Comprehend document classification endpoints, Lambda provisioned concurrency

        Example::

            # The code below shows an example of how to instantiate this type.
            # The values are placeholders you should change.
            import aws_cdk.aws_applicationautoscaling as appscaling
            import aws_cdk.core as cdk
            
            base_target_tracking_props = appscaling.BaseTargetTrackingProps(
                disable_scale_in=False,
                policy_name="policyName",
                scale_in_cooldown=cdk.Duration.minutes(30),
                scale_out_cooldown=cdk.Duration.minutes(30)
            )
        '''
        self._values: typing.Dict[str, typing.Any] = {}
        if disable_scale_in is not None:
            self._values["disable_scale_in"] = disable_scale_in
        if policy_name is not None:
            self._values["policy_name"] = policy_name
        if scale_in_cooldown is not None:
            self._values["scale_in_cooldown"] = scale_in_cooldown
        if scale_out_cooldown is not None:
            self._values["scale_out_cooldown"] = scale_out_cooldown

    @builtins.property
    def disable_scale_in(self) -> typing.Optional[builtins.bool]:
        '''Indicates whether scale in by the target tracking policy is disabled.

        If the value is true, scale in is disabled and the target tracking policy
        won't remove capacity from the scalable resource. Otherwise, scale in is
        enabled and the target tracking policy can remove capacity from the
        scalable resource.

        :default: false
        '''
        result = self._values.get("disable_scale_in")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def policy_name(self) -> typing.Optional[builtins.str]:
        '''A name for the scaling policy.

        :default: - Automatically generated name.
        '''
        result = self._values.get("policy_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def scale_in_cooldown(self) -> typing.Optional[aws_cdk.core.Duration]:
        '''Period after a scale in activity completes before another scale in activity can start.

        :default:

        Duration.seconds(300) for the following scalable targets: ECS services,
        Spot Fleet requests, EMR clusters, AppStream 2.0 fleets, Aurora DB clusters,
        Amazon SageMaker endpoint variants, Custom resources. For all other scalable
        targets, the default value is Duration.seconds(0): DynamoDB tables, DynamoDB
        global secondary indexes, Amazon Comprehend document classification endpoints,
        Lambda provisioned concurrency
        '''
        result = self._values.get("scale_in_cooldown")
        return typing.cast(typing.Optional[aws_cdk.core.Duration], result)

    @builtins.property
    def scale_out_cooldown(self) -> typing.Optional[aws_cdk.core.Duration]:
        '''Period after a scale out activity completes before another scale out activity can start.

        :default:

        Duration.seconds(300) for the following scalable targets: ECS services,
        Spot Fleet requests, EMR clusters, AppStream 2.0 fleets, Aurora DB clusters,
        Amazon SageMaker endpoint variants, Custom resources. For all other scalable
        targets, the default value is Duration.seconds(0): DynamoDB tables, DynamoDB
        global secondary indexes, Amazon Comprehend document classification endpoints,
        Lambda provisioned concurrency
        '''
        result = self._values.get("scale_out_cooldown")
        return typing.cast(typing.Optional[aws_cdk.core.Duration], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "BaseTargetTrackingProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk/aws-applicationautoscaling.BasicStepScalingPolicyProps",
    jsii_struct_bases=[],
    name_mapping={
        "adjustment_type": "adjustmentType",
        "cooldown": "cooldown",
        "evaluation_periods": "evaluationPeriods",
        "metric": "metric",
        "metric_aggregation_type": "metricAggregationType",
        "min_adjustment_magnitude": "minAdjustmentMagnitude",
        "scaling_steps": "scalingSteps",
    },
)
class BasicStepScalingPolicyProps:
    def __init__(
        self,
        *,
        adjustment_type: typing.Optional[AdjustmentType] = None,
        cooldown: typing.Optional[aws_cdk.core.Duration] = None,
        evaluation_periods: typing.Optional[jsii.Number] = None,
        metric: aws_cdk.aws_cloudwatch.IMetric,
        metric_aggregation_type: typing.Optional["MetricAggregationType"] = None,
        min_adjustment_magnitude: typing.Optional[jsii.Number] = None,
        scaling_steps: typing.Sequence["ScalingInterval"],
    ) -> None:
        '''
        :param adjustment_type: How the adjustment numbers inside 'intervals' are interpreted. Default: ChangeInCapacity
        :param cooldown: Grace period after scaling activity. Subsequent scale outs during the cooldown period are squashed so that only the biggest scale out happens. Subsequent scale ins during the cooldown period are ignored. Default: No cooldown period
        :param evaluation_periods: How many evaluation periods of the metric to wait before triggering a scaling action. Raising this value can be used to smooth out the metric, at the expense of slower response times. Default: 1
        :param metric: Metric to scale on.
        :param metric_aggregation_type: Aggregation to apply to all data points over the evaluation periods. Only has meaning if ``evaluationPeriods != 1``. Default: - The statistic from the metric if applicable (MIN, MAX, AVERAGE), otherwise AVERAGE.
        :param min_adjustment_magnitude: Minimum absolute number to adjust capacity with as result of percentage scaling. Only when using AdjustmentType = PercentChangeInCapacity, this number controls the minimum absolute effect size. Default: No minimum scaling effect
        :param scaling_steps: The intervals for scaling. Maps a range of metric values to a particular scaling behavior.

        Example::

            # capacity is of type ScalableAttribute
            # cpu_utilization is of type Metric
            
            
            capacity.scale_on_metric("ScaleToCPU",
                metric=cpu_utilization,
                scaling_steps=[appscaling.ScalingInterval(upper=10, change=-1), appscaling.ScalingInterval(lower=50, change=+1), appscaling.ScalingInterval(lower=70, change=+3)
                ],
            
                # Change this to AdjustmentType.PercentChangeInCapacity to interpret the
                # 'change' numbers before as percentages instead of capacity counts.
                adjustment_type=appscaling.AdjustmentType.CHANGE_IN_CAPACITY
            )
        '''
        self._values: typing.Dict[str, typing.Any] = {
            "metric": metric,
            "scaling_steps": scaling_steps,
        }
        if adjustment_type is not None:
            self._values["adjustment_type"] = adjustment_type
        if cooldown is not None:
            self._values["cooldown"] = cooldown
        if evaluation_periods is not None:
            self._values["evaluation_periods"] = evaluation_periods
        if metric_aggregation_type is not None:
            self._values["metric_aggregation_type"] = metric_aggregation_type
        if min_adjustment_magnitude is not None:
            self._values["min_adjustment_magnitude"] = min_adjustment_magnitude

    @builtins.property
    def adjustment_type(self) -> typing.Optional[AdjustmentType]:
        '''How the adjustment numbers inside 'intervals' are interpreted.

        :default: ChangeInCapacity
        '''
        result = self._values.get("adjustment_type")
        return typing.cast(typing.Optional[AdjustmentType], result)

    @builtins.property
    def cooldown(self) -> typing.Optional[aws_cdk.core.Duration]:
        '''Grace period after scaling activity.

        Subsequent scale outs during the cooldown period are squashed so that only
        the biggest scale out happens.

        Subsequent scale ins during the cooldown period are ignored.

        :default: No cooldown period

        :see: https://docs.aws.amazon.com/autoscaling/application/APIReference/API_StepScalingPolicyConfiguration.html
        '''
        result = self._values.get("cooldown")
        return typing.cast(typing.Optional[aws_cdk.core.Duration], result)

    @builtins.property
    def evaluation_periods(self) -> typing.Optional[jsii.Number]:
        '''How many evaluation periods of the metric to wait before triggering a scaling action.

        Raising this value can be used to smooth out the metric, at the expense
        of slower response times.

        :default: 1
        '''
        result = self._values.get("evaluation_periods")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def metric(self) -> aws_cdk.aws_cloudwatch.IMetric:
        '''Metric to scale on.'''
        result = self._values.get("metric")
        assert result is not None, "Required property 'metric' is missing"
        return typing.cast(aws_cdk.aws_cloudwatch.IMetric, result)

    @builtins.property
    def metric_aggregation_type(self) -> typing.Optional["MetricAggregationType"]:
        '''Aggregation to apply to all data points over the evaluation periods.

        Only has meaning if ``evaluationPeriods != 1``.

        :default: - The statistic from the metric if applicable (MIN, MAX, AVERAGE), otherwise AVERAGE.
        '''
        result = self._values.get("metric_aggregation_type")
        return typing.cast(typing.Optional["MetricAggregationType"], result)

    @builtins.property
    def min_adjustment_magnitude(self) -> typing.Optional[jsii.Number]:
        '''Minimum absolute number to adjust capacity with as result of percentage scaling.

        Only when using AdjustmentType = PercentChangeInCapacity, this number controls
        the minimum absolute effect size.

        :default: No minimum scaling effect
        '''
        result = self._values.get("min_adjustment_magnitude")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def scaling_steps(self) -> typing.List["ScalingInterval"]:
        '''The intervals for scaling.

        Maps a range of metric values to a particular scaling behavior.
        '''
        result = self._values.get("scaling_steps")
        assert result is not None, "Required property 'scaling_steps' is missing"
        return typing.cast(typing.List["ScalingInterval"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "BasicStepScalingPolicyProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk/aws-applicationautoscaling.BasicTargetTrackingScalingPolicyProps",
    jsii_struct_bases=[BaseTargetTrackingProps],
    name_mapping={
        "disable_scale_in": "disableScaleIn",
        "policy_name": "policyName",
        "scale_in_cooldown": "scaleInCooldown",
        "scale_out_cooldown": "scaleOutCooldown",
        "custom_metric": "customMetric",
        "predefined_metric": "predefinedMetric",
        "resource_label": "resourceLabel",
        "target_value": "targetValue",
    },
)
class BasicTargetTrackingScalingPolicyProps(BaseTargetTrackingProps):
    def __init__(
        self,
        *,
        disable_scale_in: typing.Optional[builtins.bool] = None,
        policy_name: typing.Optional[builtins.str] = None,
        scale_in_cooldown: typing.Optional[aws_cdk.core.Duration] = None,
        scale_out_cooldown: typing.Optional[aws_cdk.core.Duration] = None,
        custom_metric: typing.Optional[aws_cdk.aws_cloudwatch.IMetric] = None,
        predefined_metric: typing.Optional["PredefinedMetric"] = None,
        resource_label: typing.Optional[builtins.str] = None,
        target_value: jsii.Number,
    ) -> None:
        '''Properties for a Target Tracking policy that include the metric but exclude the target.

        :param disable_scale_in: Indicates whether scale in by the target tracking policy is disabled. If the value is true, scale in is disabled and the target tracking policy won't remove capacity from the scalable resource. Otherwise, scale in is enabled and the target tracking policy can remove capacity from the scalable resource. Default: false
        :param policy_name: A name for the scaling policy. Default: - Automatically generated name.
        :param scale_in_cooldown: Period after a scale in activity completes before another scale in activity can start. Default: Duration.seconds(300) for the following scalable targets: ECS services, Spot Fleet requests, EMR clusters, AppStream 2.0 fleets, Aurora DB clusters, Amazon SageMaker endpoint variants, Custom resources. For all other scalable targets, the default value is Duration.seconds(0): DynamoDB tables, DynamoDB global secondary indexes, Amazon Comprehend document classification endpoints, Lambda provisioned concurrency
        :param scale_out_cooldown: Period after a scale out activity completes before another scale out activity can start. Default: Duration.seconds(300) for the following scalable targets: ECS services, Spot Fleet requests, EMR clusters, AppStream 2.0 fleets, Aurora DB clusters, Amazon SageMaker endpoint variants, Custom resources. For all other scalable targets, the default value is Duration.seconds(0): DynamoDB tables, DynamoDB global secondary indexes, Amazon Comprehend document classification endpoints, Lambda provisioned concurrency
        :param custom_metric: A custom metric for application autoscaling. The metric must track utilization. Scaling out will happen if the metric is higher than the target value, scaling in will happen in the metric is lower than the target value. Exactly one of customMetric or predefinedMetric must be specified. Default: - No custom metric.
        :param predefined_metric: A predefined metric for application autoscaling. The metric must track utilization. Scaling out will happen if the metric is higher than the target value, scaling in will happen in the metric is lower than the target value. Exactly one of customMetric or predefinedMetric must be specified. Default: - No predefined metrics.
        :param resource_label: Identify the resource associated with the metric type. Only used for predefined metric ALBRequestCountPerTarget. Example value: ``app/<load-balancer-name>/<load-balancer-id>/targetgroup/<target-group-name>/<target-group-id>`` Default: - No resource label.
        :param target_value: The target value for the metric.

        Example::

            import aws_cdk.aws_lambda as lambda_
            
            # code is of type Code
            
            
            handler = lambda_.Function(self, "MyFunction",
                runtime=lambda_.Runtime.PYTHON_3_7,
                handler="index.handler",
                code=code,
            
                reserved_concurrent_executions=2
            )
            
            fn_ver = handler.add_version("CDKLambdaVersion", undefined, "demo alias", 10)
            
            target = appscaling.ScalableTarget(self, "ScalableTarget",
                service_namespace=appscaling.ServiceNamespace.LAMBDA,
                max_capacity=100,
                min_capacity=10,
                resource_id=f"function:{handler.functionName}:{fnVer.version}",
                scalable_dimension="lambda:function:ProvisionedConcurrency"
            )
            
            target.scale_to_track_metric("PceTracking",
                target_value=0.9,
                predefined_metric=appscaling.PredefinedMetric.LAMBDA_PROVISIONED_CONCURRENCY_UTILIZATION
            )
        '''
        self._values: typing.Dict[str, typing.Any] = {
            "target_value": target_value,
        }
        if disable_scale_in is not None:
            self._values["disable_scale_in"] = disable_scale_in
        if policy_name is not None:
            self._values["policy_name"] = policy_name
        if scale_in_cooldown is not None:
            self._values["scale_in_cooldown"] = scale_in_cooldown
        if scale_out_cooldown is not None:
            self._values["scale_out_cooldown"] = scale_out_cooldown
        if custom_metric is not None:
            self._values["custom_metric"] = custom_metric
        if predefined_metric is not None:
            self._values["predefined_metric"] = predefined_metric
        if resource_label is not None:
            self._values["resource_label"] = resource_label

    @builtins.property
    def disable_scale_in(self) -> typing.Optional[builtins.bool]:
        '''Indicates whether scale in by the target tracking policy is disabled.

        If the value is true, scale in is disabled and the target tracking policy
        won't remove capacity from the scalable resource. Otherwise, scale in is
        enabled and the target tracking policy can remove capacity from the
        scalable resource.

        :default: false
        '''
        result = self._values.get("disable_scale_in")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def policy_name(self) -> typing.Optional[builtins.str]:
        '''A name for the scaling policy.

        :default: - Automatically generated name.
        '''
        result = self._values.get("policy_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def scale_in_cooldown(self) -> typing.Optional[aws_cdk.core.Duration]:
        '''Period after a scale in activity completes before another scale in activity can start.

        :default:

        Duration.seconds(300) for the following scalable targets: ECS services,
        Spot Fleet requests, EMR clusters, AppStream 2.0 fleets, Aurora DB clusters,
        Amazon SageMaker endpoint variants, Custom resources. For all other scalable
        targets, the default value is Duration.seconds(0): DynamoDB tables, DynamoDB
        global secondary indexes, Amazon Comprehend document classification endpoints,
        Lambda provisioned concurrency
        '''
        result = self._values.get("scale_in_cooldown")
        return typing.cast(typing.Optional[aws_cdk.core.Duration], result)

    @builtins.property
    def scale_out_cooldown(self) -> typing.Optional[aws_cdk.core.Duration]:
        '''Period after a scale out activity completes before another scale out activity can start.

        :default:

        Duration.seconds(300) for the following scalable targets: ECS services,
        Spot Fleet requests, EMR clusters, AppStream 2.0 fleets, Aurora DB clusters,
        Amazon SageMaker endpoint variants, Custom resources. For all other scalable
        targets, the default value is Duration.seconds(0): DynamoDB tables, DynamoDB
        global secondary indexes, Amazon Comprehend document classification endpoints,
        Lambda provisioned concurrency
        '''
        result = self._values.get("scale_out_cooldown")
        return typing.cast(typing.Optional[aws_cdk.core.Duration], result)

    @builtins.property
    def custom_metric(self) -> typing.Optional[aws_cdk.aws_cloudwatch.IMetric]:
        '''A custom metric for application autoscaling.

        The metric must track utilization. Scaling out will happen if the metric is higher than
        the target value, scaling in will happen in the metric is lower than the target value.

        Exactly one of customMetric or predefinedMetric must be specified.

        :default: - No custom metric.
        '''
        result = self._values.get("custom_metric")
        return typing.cast(typing.Optional[aws_cdk.aws_cloudwatch.IMetric], result)

    @builtins.property
    def predefined_metric(self) -> typing.Optional["PredefinedMetric"]:
        '''A predefined metric for application autoscaling.

        The metric must track utilization. Scaling out will happen if the metric is higher than
        the target value, scaling in will happen in the metric is lower than the target value.

        Exactly one of customMetric or predefinedMetric must be specified.

        :default: - No predefined metrics.
        '''
        result = self._values.get("predefined_metric")
        return typing.cast(typing.Optional["PredefinedMetric"], result)

    @builtins.property
    def resource_label(self) -> typing.Optional[builtins.str]:
        '''Identify the resource associated with the metric type.

        Only used for predefined metric ALBRequestCountPerTarget.

        Example value: ``app/<load-balancer-name>/<load-balancer-id>/targetgroup/<target-group-name>/<target-group-id>``

        :default: - No resource label.
        '''
        result = self._values.get("resource_label")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def target_value(self) -> jsii.Number:
        '''The target value for the metric.'''
        result = self._values.get("target_value")
        assert result is not None, "Required property 'target_value' is missing"
        return typing.cast(jsii.Number, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "BasicTargetTrackingScalingPolicyProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.implements(aws_cdk.core.IInspectable)
class CfnScalableTarget(
    aws_cdk.core.CfnResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk/aws-applicationautoscaling.CfnScalableTarget",
):
    '''A CloudFormation ``AWS::ApplicationAutoScaling::ScalableTarget``.

    :cloudformationResource: AWS::ApplicationAutoScaling::ScalableTarget
    :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalabletarget.html

    Example::

        # The code below shows an example of how to instantiate this type.
        # The values are placeholders you should change.
        import aws_cdk.aws_applicationautoscaling as appscaling
        
        cfn_scalable_target = appscaling.CfnScalableTarget(self, "MyCfnScalableTarget",
            max_capacity=123,
            min_capacity=123,
            resource_id="resourceId",
            role_arn="roleArn",
            scalable_dimension="scalableDimension",
            service_namespace="serviceNamespace",
        
            # the properties below are optional
            scheduled_actions=[appscaling.CfnScalableTarget.ScheduledActionProperty(
                schedule="schedule",
                scheduled_action_name="scheduledActionName",
        
                # the properties below are optional
                end_time=Date(),
                scalable_target_action=appscaling.CfnScalableTarget.ScalableTargetActionProperty(
                    max_capacity=123,
                    min_capacity=123
                ),
                start_time=Date(),
                timezone="timezone"
            )],
            suspended_state=appscaling.CfnScalableTarget.SuspendedStateProperty(
                dynamic_scaling_in_suspended=False,
                dynamic_scaling_out_suspended=False,
                scheduled_scaling_suspended=False
            )
        )
    '''

    def __init__(
        self,
        scope: aws_cdk.core.Construct,
        id: builtins.str,
        *,
        max_capacity: jsii.Number,
        min_capacity: jsii.Number,
        resource_id: builtins.str,
        role_arn: builtins.str,
        scalable_dimension: builtins.str,
        scheduled_actions: typing.Optional[typing.Union[aws_cdk.core.IResolvable, typing.Sequence[typing.Union["CfnScalableTarget.ScheduledActionProperty", aws_cdk.core.IResolvable]]]] = None,
        service_namespace: builtins.str,
        suspended_state: typing.Optional[typing.Union[aws_cdk.core.IResolvable, "CfnScalableTarget.SuspendedStateProperty"]] = None,
    ) -> None:
        '''Create a new ``AWS::ApplicationAutoScaling::ScalableTarget``.

        :param scope: - scope in which this resource is defined.
        :param id: - scoped id of the resource.
        :param max_capacity: ``AWS::ApplicationAutoScaling::ScalableTarget.MaxCapacity``.
        :param min_capacity: ``AWS::ApplicationAutoScaling::ScalableTarget.MinCapacity``.
        :param resource_id: ``AWS::ApplicationAutoScaling::ScalableTarget.ResourceId``.
        :param role_arn: ``AWS::ApplicationAutoScaling::ScalableTarget.RoleARN``.
        :param scalable_dimension: ``AWS::ApplicationAutoScaling::ScalableTarget.ScalableDimension``.
        :param scheduled_actions: ``AWS::ApplicationAutoScaling::ScalableTarget.ScheduledActions``.
        :param service_namespace: ``AWS::ApplicationAutoScaling::ScalableTarget.ServiceNamespace``.
        :param suspended_state: ``AWS::ApplicationAutoScaling::ScalableTarget.SuspendedState``.
        '''
        props = CfnScalableTargetProps(
            max_capacity=max_capacity,
            min_capacity=min_capacity,
            resource_id=resource_id,
            role_arn=role_arn,
            scalable_dimension=scalable_dimension,
            scheduled_actions=scheduled_actions,
            service_namespace=service_namespace,
            suspended_state=suspended_state,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="inspect")
    def inspect(self, inspector: aws_cdk.core.TreeInspector) -> None:
        '''Examines the CloudFormation resource and discloses attributes.

        :param inspector: - tree inspector to collect and process attributes.
        '''
        return typing.cast(None, jsii.invoke(self, "inspect", [inspector]))

    @jsii.member(jsii_name="renderProperties")
    def _render_properties(
        self,
        props: typing.Mapping[builtins.str, typing.Any],
    ) -> typing.Mapping[builtins.str, typing.Any]:
        '''
        :param props: -
        '''
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "renderProperties", [props]))

    @jsii.python.classproperty # type: ignore[misc]
    @jsii.member(jsii_name="CFN_RESOURCE_TYPE_NAME")
    def CFN_RESOURCE_TYPE_NAME(cls) -> builtins.str:
        '''The CloudFormation resource type name for this resource class.'''
        return typing.cast(builtins.str, jsii.sget(cls, "CFN_RESOURCE_TYPE_NAME"))

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="cfnProperties")
    def _cfn_properties(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.get(self, "cfnProperties"))

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="maxCapacity")
    def max_capacity(self) -> jsii.Number:
        '''``AWS::ApplicationAutoScaling::ScalableTarget.MaxCapacity``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalabletarget.html#cfn-applicationautoscaling-scalabletarget-maxcapacity
        '''
        return typing.cast(jsii.Number, jsii.get(self, "maxCapacity"))

    @max_capacity.setter
    def max_capacity(self, value: jsii.Number) -> None:
        jsii.set(self, "maxCapacity", value)

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="minCapacity")
    def min_capacity(self) -> jsii.Number:
        '''``AWS::ApplicationAutoScaling::ScalableTarget.MinCapacity``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalabletarget.html#cfn-applicationautoscaling-scalabletarget-mincapacity
        '''
        return typing.cast(jsii.Number, jsii.get(self, "minCapacity"))

    @min_capacity.setter
    def min_capacity(self, value: jsii.Number) -> None:
        jsii.set(self, "minCapacity", value)

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="resourceId")
    def resource_id(self) -> builtins.str:
        '''``AWS::ApplicationAutoScaling::ScalableTarget.ResourceId``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalabletarget.html#cfn-applicationautoscaling-scalabletarget-resourceid
        '''
        return typing.cast(builtins.str, jsii.get(self, "resourceId"))

    @resource_id.setter
    def resource_id(self, value: builtins.str) -> None:
        jsii.set(self, "resourceId", value)

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="roleArn")
    def role_arn(self) -> builtins.str:
        '''``AWS::ApplicationAutoScaling::ScalableTarget.RoleARN``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalabletarget.html#cfn-applicationautoscaling-scalabletarget-rolearn
        '''
        return typing.cast(builtins.str, jsii.get(self, "roleArn"))

    @role_arn.setter
    def role_arn(self, value: builtins.str) -> None:
        jsii.set(self, "roleArn", value)

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="scalableDimension")
    def scalable_dimension(self) -> builtins.str:
        '''``AWS::ApplicationAutoScaling::ScalableTarget.ScalableDimension``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalabletarget.html#cfn-applicationautoscaling-scalabletarget-scalabledimension
        '''
        return typing.cast(builtins.str, jsii.get(self, "scalableDimension"))

    @scalable_dimension.setter
    def scalable_dimension(self, value: builtins.str) -> None:
        jsii.set(self, "scalableDimension", value)

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="scheduledActions")
    def scheduled_actions(
        self,
    ) -> typing.Optional[typing.Union[aws_cdk.core.IResolvable, typing.List[typing.Union["CfnScalableTarget.ScheduledActionProperty", aws_cdk.core.IResolvable]]]]:
        '''``AWS::ApplicationAutoScaling::ScalableTarget.ScheduledActions``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalabletarget.html#cfn-applicationautoscaling-scalabletarget-scheduledactions
        '''
        return typing.cast(typing.Optional[typing.Union[aws_cdk.core.IResolvable, typing.List[typing.Union["CfnScalableTarget.ScheduledActionProperty", aws_cdk.core.IResolvable]]]], jsii.get(self, "scheduledActions"))

    @scheduled_actions.setter
    def scheduled_actions(
        self,
        value: typing.Optional[typing.Union[aws_cdk.core.IResolvable, typing.List[typing.Union["CfnScalableTarget.ScheduledActionProperty", aws_cdk.core.IResolvable]]]],
    ) -> None:
        jsii.set(self, "scheduledActions", value)

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="serviceNamespace")
    def service_namespace(self) -> builtins.str:
        '''``AWS::ApplicationAutoScaling::ScalableTarget.ServiceNamespace``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalabletarget.html#cfn-applicationautoscaling-scalabletarget-servicenamespace
        '''
        return typing.cast(builtins.str, jsii.get(self, "serviceNamespace"))

    @service_namespace.setter
    def service_namespace(self, value: builtins.str) -> None:
        jsii.set(self, "serviceNamespace", value)

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="suspendedState")
    def suspended_state(
        self,
    ) -> typing.Optional[typing.Union[aws_cdk.core.IResolvable, "CfnScalableTarget.SuspendedStateProperty"]]:
        '''``AWS::ApplicationAutoScaling::ScalableTarget.SuspendedState``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalabletarget.html#cfn-applicationautoscaling-scalabletarget-suspendedstate
        '''
        return typing.cast(typing.Optional[typing.Union[aws_cdk.core.IResolvable, "CfnScalableTarget.SuspendedStateProperty"]], jsii.get(self, "suspendedState"))

    @suspended_state.setter
    def suspended_state(
        self,
        value: typing.Optional[typing.Union[aws_cdk.core.IResolvable, "CfnScalableTarget.SuspendedStateProperty"]],
    ) -> None:
        jsii.set(self, "suspendedState", value)

    @jsii.data_type(
        jsii_type="@aws-cdk/aws-applicationautoscaling.CfnScalableTarget.ScalableTargetActionProperty",
        jsii_struct_bases=[],
        name_mapping={"max_capacity": "maxCapacity", "min_capacity": "minCapacity"},
    )
    class ScalableTargetActionProperty:
        def __init__(
            self,
            *,
            max_capacity: typing.Optional[jsii.Number] = None,
            min_capacity: typing.Optional[jsii.Number] = None,
        ) -> None:
            '''
            :param max_capacity: ``CfnScalableTarget.ScalableTargetActionProperty.MaxCapacity``.
            :param min_capacity: ``CfnScalableTarget.ScalableTargetActionProperty.MinCapacity``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalabletarget-scalabletargetaction.html

            Example::

                # The code below shows an example of how to instantiate this type.
                # The values are placeholders you should change.
                import aws_cdk.aws_applicationautoscaling as appscaling
                
                scalable_target_action_property = appscaling.CfnScalableTarget.ScalableTargetActionProperty(
                    max_capacity=123,
                    min_capacity=123
                )
            '''
            self._values: typing.Dict[str, typing.Any] = {}
            if max_capacity is not None:
                self._values["max_capacity"] = max_capacity
            if min_capacity is not None:
                self._values["min_capacity"] = min_capacity

        @builtins.property
        def max_capacity(self) -> typing.Optional[jsii.Number]:
            '''``CfnScalableTarget.ScalableTargetActionProperty.MaxCapacity``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalabletarget-scalabletargetaction.html#cfn-applicationautoscaling-scalabletarget-scalabletargetaction-maxcapacity
            '''
            result = self._values.get("max_capacity")
            return typing.cast(typing.Optional[jsii.Number], result)

        @builtins.property
        def min_capacity(self) -> typing.Optional[jsii.Number]:
            '''``CfnScalableTarget.ScalableTargetActionProperty.MinCapacity``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalabletarget-scalabletargetaction.html#cfn-applicationautoscaling-scalabletarget-scalabletargetaction-mincapacity
            '''
            result = self._values.get("min_capacity")
            return typing.cast(typing.Optional[jsii.Number], result)

        def __eq__(self, rhs: typing.Any) -> builtins.bool:
            return isinstance(rhs, self.__class__) and rhs._values == self._values

        def __ne__(self, rhs: typing.Any) -> builtins.bool:
            return not (rhs == self)

        def __repr__(self) -> str:
            return "ScalableTargetActionProperty(%s)" % ", ".join(
                k + "=" + repr(v) for k, v in self._values.items()
            )

    @jsii.data_type(
        jsii_type="@aws-cdk/aws-applicationautoscaling.CfnScalableTarget.ScheduledActionProperty",
        jsii_struct_bases=[],
        name_mapping={
            "end_time": "endTime",
            "scalable_target_action": "scalableTargetAction",
            "schedule": "schedule",
            "scheduled_action_name": "scheduledActionName",
            "start_time": "startTime",
            "timezone": "timezone",
        },
    )
    class ScheduledActionProperty:
        def __init__(
            self,
            *,
            end_time: typing.Optional[typing.Union[aws_cdk.core.IResolvable, datetime.datetime]] = None,
            scalable_target_action: typing.Optional[typing.Union[aws_cdk.core.IResolvable, "CfnScalableTarget.ScalableTargetActionProperty"]] = None,
            schedule: builtins.str,
            scheduled_action_name: builtins.str,
            start_time: typing.Optional[typing.Union[aws_cdk.core.IResolvable, datetime.datetime]] = None,
            timezone: typing.Optional[builtins.str] = None,
        ) -> None:
            '''
            :param end_time: ``CfnScalableTarget.ScheduledActionProperty.EndTime``.
            :param scalable_target_action: ``CfnScalableTarget.ScheduledActionProperty.ScalableTargetAction``.
            :param schedule: ``CfnScalableTarget.ScheduledActionProperty.Schedule``.
            :param scheduled_action_name: ``CfnScalableTarget.ScheduledActionProperty.ScheduledActionName``.
            :param start_time: ``CfnScalableTarget.ScheduledActionProperty.StartTime``.
            :param timezone: ``CfnScalableTarget.ScheduledActionProperty.Timezone``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalabletarget-scheduledaction.html

            Example::

                # The code below shows an example of how to instantiate this type.
                # The values are placeholders you should change.
                import aws_cdk.aws_applicationautoscaling as appscaling
                
                scheduled_action_property = appscaling.CfnScalableTarget.ScheduledActionProperty(
                    schedule="schedule",
                    scheduled_action_name="scheduledActionName",
                
                    # the properties below are optional
                    end_time=Date(),
                    scalable_target_action=appscaling.CfnScalableTarget.ScalableTargetActionProperty(
                        max_capacity=123,
                        min_capacity=123
                    ),
                    start_time=Date(),
                    timezone="timezone"
                )
            '''
            self._values: typing.Dict[str, typing.Any] = {
                "schedule": schedule,
                "scheduled_action_name": scheduled_action_name,
            }
            if end_time is not None:
                self._values["end_time"] = end_time
            if scalable_target_action is not None:
                self._values["scalable_target_action"] = scalable_target_action
            if start_time is not None:
                self._values["start_time"] = start_time
            if timezone is not None:
                self._values["timezone"] = timezone

        @builtins.property
        def end_time(
            self,
        ) -> typing.Optional[typing.Union[aws_cdk.core.IResolvable, datetime.datetime]]:
            '''``CfnScalableTarget.ScheduledActionProperty.EndTime``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalabletarget-scheduledaction.html#cfn-applicationautoscaling-scalabletarget-scheduledaction-endtime
            '''
            result = self._values.get("end_time")
            return typing.cast(typing.Optional[typing.Union[aws_cdk.core.IResolvable, datetime.datetime]], result)

        @builtins.property
        def scalable_target_action(
            self,
        ) -> typing.Optional[typing.Union[aws_cdk.core.IResolvable, "CfnScalableTarget.ScalableTargetActionProperty"]]:
            '''``CfnScalableTarget.ScheduledActionProperty.ScalableTargetAction``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalabletarget-scheduledaction.html#cfn-applicationautoscaling-scalabletarget-scheduledaction-scalabletargetaction
            '''
            result = self._values.get("scalable_target_action")
            return typing.cast(typing.Optional[typing.Union[aws_cdk.core.IResolvable, "CfnScalableTarget.ScalableTargetActionProperty"]], result)

        @builtins.property
        def schedule(self) -> builtins.str:
            '''``CfnScalableTarget.ScheduledActionProperty.Schedule``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalabletarget-scheduledaction.html#cfn-applicationautoscaling-scalabletarget-scheduledaction-schedule
            '''
            result = self._values.get("schedule")
            assert result is not None, "Required property 'schedule' is missing"
            return typing.cast(builtins.str, result)

        @builtins.property
        def scheduled_action_name(self) -> builtins.str:
            '''``CfnScalableTarget.ScheduledActionProperty.ScheduledActionName``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalabletarget-scheduledaction.html#cfn-applicationautoscaling-scalabletarget-scheduledaction-scheduledactionname
            '''
            result = self._values.get("scheduled_action_name")
            assert result is not None, "Required property 'scheduled_action_name' is missing"
            return typing.cast(builtins.str, result)

        @builtins.property
        def start_time(
            self,
        ) -> typing.Optional[typing.Union[aws_cdk.core.IResolvable, datetime.datetime]]:
            '''``CfnScalableTarget.ScheduledActionProperty.StartTime``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalabletarget-scheduledaction.html#cfn-applicationautoscaling-scalabletarget-scheduledaction-starttime
            '''
            result = self._values.get("start_time")
            return typing.cast(typing.Optional[typing.Union[aws_cdk.core.IResolvable, datetime.datetime]], result)

        @builtins.property
        def timezone(self) -> typing.Optional[builtins.str]:
            '''``CfnScalableTarget.ScheduledActionProperty.Timezone``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalabletarget-scheduledaction.html#cfn-applicationautoscaling-scalabletarget-scheduledaction-timezone
            '''
            result = self._values.get("timezone")
            return typing.cast(typing.Optional[builtins.str], result)

        def __eq__(self, rhs: typing.Any) -> builtins.bool:
            return isinstance(rhs, self.__class__) and rhs._values == self._values

        def __ne__(self, rhs: typing.Any) -> builtins.bool:
            return not (rhs == self)

        def __repr__(self) -> str:
            return "ScheduledActionProperty(%s)" % ", ".join(
                k + "=" + repr(v) for k, v in self._values.items()
            )

    @jsii.data_type(
        jsii_type="@aws-cdk/aws-applicationautoscaling.CfnScalableTarget.SuspendedStateProperty",
        jsii_struct_bases=[],
        name_mapping={
            "dynamic_scaling_in_suspended": "dynamicScalingInSuspended",
            "dynamic_scaling_out_suspended": "dynamicScalingOutSuspended",
            "scheduled_scaling_suspended": "scheduledScalingSuspended",
        },
    )
    class SuspendedStateProperty:
        def __init__(
            self,
            *,
            dynamic_scaling_in_suspended: typing.Optional[typing.Union[builtins.bool, aws_cdk.core.IResolvable]] = None,
            dynamic_scaling_out_suspended: typing.Optional[typing.Union[builtins.bool, aws_cdk.core.IResolvable]] = None,
            scheduled_scaling_suspended: typing.Optional[typing.Union[builtins.bool, aws_cdk.core.IResolvable]] = None,
        ) -> None:
            '''
            :param dynamic_scaling_in_suspended: ``CfnScalableTarget.SuspendedStateProperty.DynamicScalingInSuspended``.
            :param dynamic_scaling_out_suspended: ``CfnScalableTarget.SuspendedStateProperty.DynamicScalingOutSuspended``.
            :param scheduled_scaling_suspended: ``CfnScalableTarget.SuspendedStateProperty.ScheduledScalingSuspended``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalabletarget-suspendedstate.html

            Example::

                # The code below shows an example of how to instantiate this type.
                # The values are placeholders you should change.
                import aws_cdk.aws_applicationautoscaling as appscaling
                
                suspended_state_property = appscaling.CfnScalableTarget.SuspendedStateProperty(
                    dynamic_scaling_in_suspended=False,
                    dynamic_scaling_out_suspended=False,
                    scheduled_scaling_suspended=False
                )
            '''
            self._values: typing.Dict[str, typing.Any] = {}
            if dynamic_scaling_in_suspended is not None:
                self._values["dynamic_scaling_in_suspended"] = dynamic_scaling_in_suspended
            if dynamic_scaling_out_suspended is not None:
                self._values["dynamic_scaling_out_suspended"] = dynamic_scaling_out_suspended
            if scheduled_scaling_suspended is not None:
                self._values["scheduled_scaling_suspended"] = scheduled_scaling_suspended

        @builtins.property
        def dynamic_scaling_in_suspended(
            self,
        ) -> typing.Optional[typing.Union[builtins.bool, aws_cdk.core.IResolvable]]:
            '''``CfnScalableTarget.SuspendedStateProperty.DynamicScalingInSuspended``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalabletarget-suspendedstate.html#cfn-applicationautoscaling-scalabletarget-suspendedstate-dynamicscalinginsuspended
            '''
            result = self._values.get("dynamic_scaling_in_suspended")
            return typing.cast(typing.Optional[typing.Union[builtins.bool, aws_cdk.core.IResolvable]], result)

        @builtins.property
        def dynamic_scaling_out_suspended(
            self,
        ) -> typing.Optional[typing.Union[builtins.bool, aws_cdk.core.IResolvable]]:
            '''``CfnScalableTarget.SuspendedStateProperty.DynamicScalingOutSuspended``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalabletarget-suspendedstate.html#cfn-applicationautoscaling-scalabletarget-suspendedstate-dynamicscalingoutsuspended
            '''
            result = self._values.get("dynamic_scaling_out_suspended")
            return typing.cast(typing.Optional[typing.Union[builtins.bool, aws_cdk.core.IResolvable]], result)

        @builtins.property
        def scheduled_scaling_suspended(
            self,
        ) -> typing.Optional[typing.Union[builtins.bool, aws_cdk.core.IResolvable]]:
            '''``CfnScalableTarget.SuspendedStateProperty.ScheduledScalingSuspended``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalabletarget-suspendedstate.html#cfn-applicationautoscaling-scalabletarget-suspendedstate-scheduledscalingsuspended
            '''
            result = self._values.get("scheduled_scaling_suspended")
            return typing.cast(typing.Optional[typing.Union[builtins.bool, aws_cdk.core.IResolvable]], result)

        def __eq__(self, rhs: typing.Any) -> builtins.bool:
            return isinstance(rhs, self.__class__) and rhs._values == self._values

        def __ne__(self, rhs: typing.Any) -> builtins.bool:
            return not (rhs == self)

        def __repr__(self) -> str:
            return "SuspendedStateProperty(%s)" % ", ".join(
                k + "=" + repr(v) for k, v in self._values.items()
            )


@jsii.data_type(
    jsii_type="@aws-cdk/aws-applicationautoscaling.CfnScalableTargetProps",
    jsii_struct_bases=[],
    name_mapping={
        "max_capacity": "maxCapacity",
        "min_capacity": "minCapacity",
        "resource_id": "resourceId",
        "role_arn": "roleArn",
        "scalable_dimension": "scalableDimension",
        "scheduled_actions": "scheduledActions",
        "service_namespace": "serviceNamespace",
        "suspended_state": "suspendedState",
    },
)
class CfnScalableTargetProps:
    def __init__(
        self,
        *,
        max_capacity: jsii.Number,
        min_capacity: jsii.Number,
        resource_id: builtins.str,
        role_arn: builtins.str,
        scalable_dimension: builtins.str,
        scheduled_actions: typing.Optional[typing.Union[aws_cdk.core.IResolvable, typing.Sequence[typing.Union[CfnScalableTarget.ScheduledActionProperty, aws_cdk.core.IResolvable]]]] = None,
        service_namespace: builtins.str,
        suspended_state: typing.Optional[typing.Union[aws_cdk.core.IResolvable, CfnScalableTarget.SuspendedStateProperty]] = None,
    ) -> None:
        '''Properties for defining a ``AWS::ApplicationAutoScaling::ScalableTarget``.

        :param max_capacity: ``AWS::ApplicationAutoScaling::ScalableTarget.MaxCapacity``.
        :param min_capacity: ``AWS::ApplicationAutoScaling::ScalableTarget.MinCapacity``.
        :param resource_id: ``AWS::ApplicationAutoScaling::ScalableTarget.ResourceId``.
        :param role_arn: ``AWS::ApplicationAutoScaling::ScalableTarget.RoleARN``.
        :param scalable_dimension: ``AWS::ApplicationAutoScaling::ScalableTarget.ScalableDimension``.
        :param scheduled_actions: ``AWS::ApplicationAutoScaling::ScalableTarget.ScheduledActions``.
        :param service_namespace: ``AWS::ApplicationAutoScaling::ScalableTarget.ServiceNamespace``.
        :param suspended_state: ``AWS::ApplicationAutoScaling::ScalableTarget.SuspendedState``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalabletarget.html

        Example::

            # The code below shows an example of how to instantiate this type.
            # The values are placeholders you should change.
            import aws_cdk.aws_applicationautoscaling as appscaling
            
            cfn_scalable_target_props = appscaling.CfnScalableTargetProps(
                max_capacity=123,
                min_capacity=123,
                resource_id="resourceId",
                role_arn="roleArn",
                scalable_dimension="scalableDimension",
                service_namespace="serviceNamespace",
            
                # the properties below are optional
                scheduled_actions=[appscaling.CfnScalableTarget.ScheduledActionProperty(
                    schedule="schedule",
                    scheduled_action_name="scheduledActionName",
            
                    # the properties below are optional
                    end_time=Date(),
                    scalable_target_action=appscaling.CfnScalableTarget.ScalableTargetActionProperty(
                        max_capacity=123,
                        min_capacity=123
                    ),
                    start_time=Date(),
                    timezone="timezone"
                )],
                suspended_state=appscaling.CfnScalableTarget.SuspendedStateProperty(
                    dynamic_scaling_in_suspended=False,
                    dynamic_scaling_out_suspended=False,
                    scheduled_scaling_suspended=False
                )
            )
        '''
        self._values: typing.Dict[str, typing.Any] = {
            "max_capacity": max_capacity,
            "min_capacity": min_capacity,
            "resource_id": resource_id,
            "role_arn": role_arn,
            "scalable_dimension": scalable_dimension,
            "service_namespace": service_namespace,
        }
        if scheduled_actions is not None:
            self._values["scheduled_actions"] = scheduled_actions
        if suspended_state is not None:
            self._values["suspended_state"] = suspended_state

    @builtins.property
    def max_capacity(self) -> jsii.Number:
        '''``AWS::ApplicationAutoScaling::ScalableTarget.MaxCapacity``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalabletarget.html#cfn-applicationautoscaling-scalabletarget-maxcapacity
        '''
        result = self._values.get("max_capacity")
        assert result is not None, "Required property 'max_capacity' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def min_capacity(self) -> jsii.Number:
        '''``AWS::ApplicationAutoScaling::ScalableTarget.MinCapacity``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalabletarget.html#cfn-applicationautoscaling-scalabletarget-mincapacity
        '''
        result = self._values.get("min_capacity")
        assert result is not None, "Required property 'min_capacity' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def resource_id(self) -> builtins.str:
        '''``AWS::ApplicationAutoScaling::ScalableTarget.ResourceId``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalabletarget.html#cfn-applicationautoscaling-scalabletarget-resourceid
        '''
        result = self._values.get("resource_id")
        assert result is not None, "Required property 'resource_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def role_arn(self) -> builtins.str:
        '''``AWS::ApplicationAutoScaling::ScalableTarget.RoleARN``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalabletarget.html#cfn-applicationautoscaling-scalabletarget-rolearn
        '''
        result = self._values.get("role_arn")
        assert result is not None, "Required property 'role_arn' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def scalable_dimension(self) -> builtins.str:
        '''``AWS::ApplicationAutoScaling::ScalableTarget.ScalableDimension``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalabletarget.html#cfn-applicationautoscaling-scalabletarget-scalabledimension
        '''
        result = self._values.get("scalable_dimension")
        assert result is not None, "Required property 'scalable_dimension' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def scheduled_actions(
        self,
    ) -> typing.Optional[typing.Union[aws_cdk.core.IResolvable, typing.List[typing.Union[CfnScalableTarget.ScheduledActionProperty, aws_cdk.core.IResolvable]]]]:
        '''``AWS::ApplicationAutoScaling::ScalableTarget.ScheduledActions``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalabletarget.html#cfn-applicationautoscaling-scalabletarget-scheduledactions
        '''
        result = self._values.get("scheduled_actions")
        return typing.cast(typing.Optional[typing.Union[aws_cdk.core.IResolvable, typing.List[typing.Union[CfnScalableTarget.ScheduledActionProperty, aws_cdk.core.IResolvable]]]], result)

    @builtins.property
    def service_namespace(self) -> builtins.str:
        '''``AWS::ApplicationAutoScaling::ScalableTarget.ServiceNamespace``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalabletarget.html#cfn-applicationautoscaling-scalabletarget-servicenamespace
        '''
        result = self._values.get("service_namespace")
        assert result is not None, "Required property 'service_namespace' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def suspended_state(
        self,
    ) -> typing.Optional[typing.Union[aws_cdk.core.IResolvable, CfnScalableTarget.SuspendedStateProperty]]:
        '''``AWS::ApplicationAutoScaling::ScalableTarget.SuspendedState``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalabletarget.html#cfn-applicationautoscaling-scalabletarget-suspendedstate
        '''
        result = self._values.get("suspended_state")
        return typing.cast(typing.Optional[typing.Union[aws_cdk.core.IResolvable, CfnScalableTarget.SuspendedStateProperty]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CfnScalableTargetProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.implements(aws_cdk.core.IInspectable)
class CfnScalingPolicy(
    aws_cdk.core.CfnResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk/aws-applicationautoscaling.CfnScalingPolicy",
):
    '''A CloudFormation ``AWS::ApplicationAutoScaling::ScalingPolicy``.

    :cloudformationResource: AWS::ApplicationAutoScaling::ScalingPolicy
    :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalingpolicy.html

    Example::

        # The code below shows an example of how to instantiate this type.
        # The values are placeholders you should change.
        import aws_cdk.aws_applicationautoscaling as appscaling
        
        cfn_scaling_policy = appscaling.CfnScalingPolicy(self, "MyCfnScalingPolicy",
            policy_name="policyName",
            policy_type="policyType",
        
            # the properties below are optional
            resource_id="resourceId",
            scalable_dimension="scalableDimension",
            scaling_target_id="scalingTargetId",
            service_namespace="serviceNamespace",
            step_scaling_policy_configuration=appscaling.CfnScalingPolicy.StepScalingPolicyConfigurationProperty(
                adjustment_type="adjustmentType",
                cooldown=123,
                metric_aggregation_type="metricAggregationType",
                min_adjustment_magnitude=123,
                step_adjustments=[appscaling.CfnScalingPolicy.StepAdjustmentProperty(
                    scaling_adjustment=123,
        
                    # the properties below are optional
                    metric_interval_lower_bound=123,
                    metric_interval_upper_bound=123
                )]
            ),
            target_tracking_scaling_policy_configuration=appscaling.CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty(
                target_value=123,
        
                # the properties below are optional
                customized_metric_specification=appscaling.CfnScalingPolicy.CustomizedMetricSpecificationProperty(
                    metric_name="metricName",
                    namespace="namespace",
                    statistic="statistic",
        
                    # the properties below are optional
                    dimensions=[appscaling.CfnScalingPolicy.MetricDimensionProperty(
                        name="name",
                        value="value"
                    )],
                    unit="unit"
                ),
                disable_scale_in=False,
                predefined_metric_specification=appscaling.CfnScalingPolicy.PredefinedMetricSpecificationProperty(
                    predefined_metric_type="predefinedMetricType",
        
                    # the properties below are optional
                    resource_label="resourceLabel"
                ),
                scale_in_cooldown=123,
                scale_out_cooldown=123
            )
        )
    '''

    def __init__(
        self,
        scope: aws_cdk.core.Construct,
        id: builtins.str,
        *,
        policy_name: builtins.str,
        policy_type: builtins.str,
        resource_id: typing.Optional[builtins.str] = None,
        scalable_dimension: typing.Optional[builtins.str] = None,
        scaling_target_id: typing.Optional[builtins.str] = None,
        service_namespace: typing.Optional[builtins.str] = None,
        step_scaling_policy_configuration: typing.Optional[typing.Union[aws_cdk.core.IResolvable, "CfnScalingPolicy.StepScalingPolicyConfigurationProperty"]] = None,
        target_tracking_scaling_policy_configuration: typing.Optional[typing.Union[aws_cdk.core.IResolvable, "CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty"]] = None,
    ) -> None:
        '''Create a new ``AWS::ApplicationAutoScaling::ScalingPolicy``.

        :param scope: - scope in which this resource is defined.
        :param id: - scoped id of the resource.
        :param policy_name: ``AWS::ApplicationAutoScaling::ScalingPolicy.PolicyName``.
        :param policy_type: ``AWS::ApplicationAutoScaling::ScalingPolicy.PolicyType``.
        :param resource_id: ``AWS::ApplicationAutoScaling::ScalingPolicy.ResourceId``.
        :param scalable_dimension: ``AWS::ApplicationAutoScaling::ScalingPolicy.ScalableDimension``.
        :param scaling_target_id: ``AWS::ApplicationAutoScaling::ScalingPolicy.ScalingTargetId``.
        :param service_namespace: ``AWS::ApplicationAutoScaling::ScalingPolicy.ServiceNamespace``.
        :param step_scaling_policy_configuration: ``AWS::ApplicationAutoScaling::ScalingPolicy.StepScalingPolicyConfiguration``.
        :param target_tracking_scaling_policy_configuration: ``AWS::ApplicationAutoScaling::ScalingPolicy.TargetTrackingScalingPolicyConfiguration``.
        '''
        props = CfnScalingPolicyProps(
            policy_name=policy_name,
            policy_type=policy_type,
            resource_id=resource_id,
            scalable_dimension=scalable_dimension,
            scaling_target_id=scaling_target_id,
            service_namespace=service_namespace,
            step_scaling_policy_configuration=step_scaling_policy_configuration,
            target_tracking_scaling_policy_configuration=target_tracking_scaling_policy_configuration,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="inspect")
    def inspect(self, inspector: aws_cdk.core.TreeInspector) -> None:
        '''Examines the CloudFormation resource and discloses attributes.

        :param inspector: - tree inspector to collect and process attributes.
        '''
        return typing.cast(None, jsii.invoke(self, "inspect", [inspector]))

    @jsii.member(jsii_name="renderProperties")
    def _render_properties(
        self,
        props: typing.Mapping[builtins.str, typing.Any],
    ) -> typing.Mapping[builtins.str, typing.Any]:
        '''
        :param props: -
        '''
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "renderProperties", [props]))

    @jsii.python.classproperty # type: ignore[misc]
    @jsii.member(jsii_name="CFN_RESOURCE_TYPE_NAME")
    def CFN_RESOURCE_TYPE_NAME(cls) -> builtins.str:
        '''The CloudFormation resource type name for this resource class.'''
        return typing.cast(builtins.str, jsii.sget(cls, "CFN_RESOURCE_TYPE_NAME"))

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="cfnProperties")
    def _cfn_properties(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.get(self, "cfnProperties"))

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="policyName")
    def policy_name(self) -> builtins.str:
        '''``AWS::ApplicationAutoScaling::ScalingPolicy.PolicyName``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalingpolicy.html#cfn-applicationautoscaling-scalingpolicy-policyname
        '''
        return typing.cast(builtins.str, jsii.get(self, "policyName"))

    @policy_name.setter
    def policy_name(self, value: builtins.str) -> None:
        jsii.set(self, "policyName", value)

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="policyType")
    def policy_type(self) -> builtins.str:
        '''``AWS::ApplicationAutoScaling::ScalingPolicy.PolicyType``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalingpolicy.html#cfn-applicationautoscaling-scalingpolicy-policytype
        '''
        return typing.cast(builtins.str, jsii.get(self, "policyType"))

    @policy_type.setter
    def policy_type(self, value: builtins.str) -> None:
        jsii.set(self, "policyType", value)

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="resourceId")
    def resource_id(self) -> typing.Optional[builtins.str]:
        '''``AWS::ApplicationAutoScaling::ScalingPolicy.ResourceId``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalingpolicy.html#cfn-applicationautoscaling-scalingpolicy-resourceid
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "resourceId"))

    @resource_id.setter
    def resource_id(self, value: typing.Optional[builtins.str]) -> None:
        jsii.set(self, "resourceId", value)

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="scalableDimension")
    def scalable_dimension(self) -> typing.Optional[builtins.str]:
        '''``AWS::ApplicationAutoScaling::ScalingPolicy.ScalableDimension``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalingpolicy.html#cfn-applicationautoscaling-scalingpolicy-scalabledimension
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "scalableDimension"))

    @scalable_dimension.setter
    def scalable_dimension(self, value: typing.Optional[builtins.str]) -> None:
        jsii.set(self, "scalableDimension", value)

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="scalingTargetId")
    def scaling_target_id(self) -> typing.Optional[builtins.str]:
        '''``AWS::ApplicationAutoScaling::ScalingPolicy.ScalingTargetId``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalingpolicy.html#cfn-applicationautoscaling-scalingpolicy-scalingtargetid
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "scalingTargetId"))

    @scaling_target_id.setter
    def scaling_target_id(self, value: typing.Optional[builtins.str]) -> None:
        jsii.set(self, "scalingTargetId", value)

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="serviceNamespace")
    def service_namespace(self) -> typing.Optional[builtins.str]:
        '''``AWS::ApplicationAutoScaling::ScalingPolicy.ServiceNamespace``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalingpolicy.html#cfn-applicationautoscaling-scalingpolicy-servicenamespace
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "serviceNamespace"))

    @service_namespace.setter
    def service_namespace(self, value: typing.Optional[builtins.str]) -> None:
        jsii.set(self, "serviceNamespace", value)

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="stepScalingPolicyConfiguration")
    def step_scaling_policy_configuration(
        self,
    ) -> typing.Optional[typing.Union[aws_cdk.core.IResolvable, "CfnScalingPolicy.StepScalingPolicyConfigurationProperty"]]:
        '''``AWS::ApplicationAutoScaling::ScalingPolicy.StepScalingPolicyConfiguration``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalingpolicy.html#cfn-applicationautoscaling-scalingpolicy-stepscalingpolicyconfiguration
        '''
        return typing.cast(typing.Optional[typing.Union[aws_cdk.core.IResolvable, "CfnScalingPolicy.StepScalingPolicyConfigurationProperty"]], jsii.get(self, "stepScalingPolicyConfiguration"))

    @step_scaling_policy_configuration.setter
    def step_scaling_policy_configuration(
        self,
        value: typing.Optional[typing.Union[aws_cdk.core.IResolvable, "CfnScalingPolicy.StepScalingPolicyConfigurationProperty"]],
    ) -> None:
        jsii.set(self, "stepScalingPolicyConfiguration", value)

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="targetTrackingScalingPolicyConfiguration")
    def target_tracking_scaling_policy_configuration(
        self,
    ) -> typing.Optional[typing.Union[aws_cdk.core.IResolvable, "CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty"]]:
        '''``AWS::ApplicationAutoScaling::ScalingPolicy.TargetTrackingScalingPolicyConfiguration``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalingpolicy.html#cfn-applicationautoscaling-scalingpolicy-targettrackingscalingpolicyconfiguration
        '''
        return typing.cast(typing.Optional[typing.Union[aws_cdk.core.IResolvable, "CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty"]], jsii.get(self, "targetTrackingScalingPolicyConfiguration"))

    @target_tracking_scaling_policy_configuration.setter
    def target_tracking_scaling_policy_configuration(
        self,
        value: typing.Optional[typing.Union[aws_cdk.core.IResolvable, "CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty"]],
    ) -> None:
        jsii.set(self, "targetTrackingScalingPolicyConfiguration", value)

    @jsii.data_type(
        jsii_type="@aws-cdk/aws-applicationautoscaling.CfnScalingPolicy.CustomizedMetricSpecificationProperty",
        jsii_struct_bases=[],
        name_mapping={
            "dimensions": "dimensions",
            "metric_name": "metricName",
            "namespace": "namespace",
            "statistic": "statistic",
            "unit": "unit",
        },
    )
    class CustomizedMetricSpecificationProperty:
        def __init__(
            self,
            *,
            dimensions: typing.Optional[typing.Union[aws_cdk.core.IResolvable, typing.Sequence[typing.Union[aws_cdk.core.IResolvable, "CfnScalingPolicy.MetricDimensionProperty"]]]] = None,
            metric_name: builtins.str,
            namespace: builtins.str,
            statistic: builtins.str,
            unit: typing.Optional[builtins.str] = None,
        ) -> None:
            '''
            :param dimensions: ``CfnScalingPolicy.CustomizedMetricSpecificationProperty.Dimensions``.
            :param metric_name: ``CfnScalingPolicy.CustomizedMetricSpecificationProperty.MetricName``.
            :param namespace: ``CfnScalingPolicy.CustomizedMetricSpecificationProperty.Namespace``.
            :param statistic: ``CfnScalingPolicy.CustomizedMetricSpecificationProperty.Statistic``.
            :param unit: ``CfnScalingPolicy.CustomizedMetricSpecificationProperty.Unit``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-customizedmetricspecification.html

            Example::

                # The code below shows an example of how to instantiate this type.
                # The values are placeholders you should change.
                import aws_cdk.aws_applicationautoscaling as appscaling
                
                customized_metric_specification_property = appscaling.CfnScalingPolicy.CustomizedMetricSpecificationProperty(
                    metric_name="metricName",
                    namespace="namespace",
                    statistic="statistic",
                
                    # the properties below are optional
                    dimensions=[appscaling.CfnScalingPolicy.MetricDimensionProperty(
                        name="name",
                        value="value"
                    )],
                    unit="unit"
                )
            '''
            self._values: typing.Dict[str, typing.Any] = {
                "metric_name": metric_name,
                "namespace": namespace,
                "statistic": statistic,
            }
            if dimensions is not None:
                self._values["dimensions"] = dimensions
            if unit is not None:
                self._values["unit"] = unit

        @builtins.property
        def dimensions(
            self,
        ) -> typing.Optional[typing.Union[aws_cdk.core.IResolvable, typing.List[typing.Union[aws_cdk.core.IResolvable, "CfnScalingPolicy.MetricDimensionProperty"]]]]:
            '''``CfnScalingPolicy.CustomizedMetricSpecificationProperty.Dimensions``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-customizedmetricspecification.html#cfn-applicationautoscaling-scalingpolicy-customizedmetricspecification-dimensions
            '''
            result = self._values.get("dimensions")
            return typing.cast(typing.Optional[typing.Union[aws_cdk.core.IResolvable, typing.List[typing.Union[aws_cdk.core.IResolvable, "CfnScalingPolicy.MetricDimensionProperty"]]]], result)

        @builtins.property
        def metric_name(self) -> builtins.str:
            '''``CfnScalingPolicy.CustomizedMetricSpecificationProperty.MetricName``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-customizedmetricspecification.html#cfn-applicationautoscaling-scalingpolicy-customizedmetricspecification-metricname
            '''
            result = self._values.get("metric_name")
            assert result is not None, "Required property 'metric_name' is missing"
            return typing.cast(builtins.str, result)

        @builtins.property
        def namespace(self) -> builtins.str:
            '''``CfnScalingPolicy.CustomizedMetricSpecificationProperty.Namespace``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-customizedmetricspecification.html#cfn-applicationautoscaling-scalingpolicy-customizedmetricspecification-namespace
            '''
            result = self._values.get("namespace")
            assert result is not None, "Required property 'namespace' is missing"
            return typing.cast(builtins.str, result)

        @builtins.property
        def statistic(self) -> builtins.str:
            '''``CfnScalingPolicy.CustomizedMetricSpecificationProperty.Statistic``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-customizedmetricspecification.html#cfn-applicationautoscaling-scalingpolicy-customizedmetricspecification-statistic
            '''
            result = self._values.get("statistic")
            assert result is not None, "Required property 'statistic' is missing"
            return typing.cast(builtins.str, result)

        @builtins.property
        def unit(self) -> typing.Optional[builtins.str]:
            '''``CfnScalingPolicy.CustomizedMetricSpecificationProperty.Unit``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-customizedmetricspecification.html#cfn-applicationautoscaling-scalingpolicy-customizedmetricspecification-unit
            '''
            result = self._values.get("unit")
            return typing.cast(typing.Optional[builtins.str], result)

        def __eq__(self, rhs: typing.Any) -> builtins.bool:
            return isinstance(rhs, self.__class__) and rhs._values == self._values

        def __ne__(self, rhs: typing.Any) -> builtins.bool:
            return not (rhs == self)

        def __repr__(self) -> str:
            return "CustomizedMetricSpecificationProperty(%s)" % ", ".join(
                k + "=" + repr(v) for k, v in self._values.items()
            )

    @jsii.data_type(
        jsii_type="@aws-cdk/aws-applicationautoscaling.CfnScalingPolicy.MetricDimensionProperty",
        jsii_struct_bases=[],
        name_mapping={"name": "name", "value": "value"},
    )
    class MetricDimensionProperty:
        def __init__(self, *, name: builtins.str, value: builtins.str) -> None:
            '''
            :param name: ``CfnScalingPolicy.MetricDimensionProperty.Name``.
            :param value: ``CfnScalingPolicy.MetricDimensionProperty.Value``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-metricdimension.html

            Example::

                # The code below shows an example of how to instantiate this type.
                # The values are placeholders you should change.
                import aws_cdk.aws_applicationautoscaling as appscaling
                
                metric_dimension_property = appscaling.CfnScalingPolicy.MetricDimensionProperty(
                    name="name",
                    value="value"
                )
            '''
            self._values: typing.Dict[str, typing.Any] = {
                "name": name,
                "value": value,
            }

        @builtins.property
        def name(self) -> builtins.str:
            '''``CfnScalingPolicy.MetricDimensionProperty.Name``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-metricdimension.html#cfn-applicationautoscaling-scalingpolicy-metricdimension-name
            '''
            result = self._values.get("name")
            assert result is not None, "Required property 'name' is missing"
            return typing.cast(builtins.str, result)

        @builtins.property
        def value(self) -> builtins.str:
            '''``CfnScalingPolicy.MetricDimensionProperty.Value``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-metricdimension.html#cfn-applicationautoscaling-scalingpolicy-metricdimension-value
            '''
            result = self._values.get("value")
            assert result is not None, "Required property 'value' is missing"
            return typing.cast(builtins.str, result)

        def __eq__(self, rhs: typing.Any) -> builtins.bool:
            return isinstance(rhs, self.__class__) and rhs._values == self._values

        def __ne__(self, rhs: typing.Any) -> builtins.bool:
            return not (rhs == self)

        def __repr__(self) -> str:
            return "MetricDimensionProperty(%s)" % ", ".join(
                k + "=" + repr(v) for k, v in self._values.items()
            )

    @jsii.data_type(
        jsii_type="@aws-cdk/aws-applicationautoscaling.CfnScalingPolicy.PredefinedMetricSpecificationProperty",
        jsii_struct_bases=[],
        name_mapping={
            "predefined_metric_type": "predefinedMetricType",
            "resource_label": "resourceLabel",
        },
    )
    class PredefinedMetricSpecificationProperty:
        def __init__(
            self,
            *,
            predefined_metric_type: builtins.str,
            resource_label: typing.Optional[builtins.str] = None,
        ) -> None:
            '''
            :param predefined_metric_type: ``CfnScalingPolicy.PredefinedMetricSpecificationProperty.PredefinedMetricType``.
            :param resource_label: ``CfnScalingPolicy.PredefinedMetricSpecificationProperty.ResourceLabel``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-predefinedmetricspecification.html

            Example::

                # The code below shows an example of how to instantiate this type.
                # The values are placeholders you should change.
                import aws_cdk.aws_applicationautoscaling as appscaling
                
                predefined_metric_specification_property = appscaling.CfnScalingPolicy.PredefinedMetricSpecificationProperty(
                    predefined_metric_type="predefinedMetricType",
                
                    # the properties below are optional
                    resource_label="resourceLabel"
                )
            '''
            self._values: typing.Dict[str, typing.Any] = {
                "predefined_metric_type": predefined_metric_type,
            }
            if resource_label is not None:
                self._values["resource_label"] = resource_label

        @builtins.property
        def predefined_metric_type(self) -> builtins.str:
            '''``CfnScalingPolicy.PredefinedMetricSpecificationProperty.PredefinedMetricType``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-predefinedmetricspecification.html#cfn-applicationautoscaling-scalingpolicy-predefinedmetricspecification-predefinedmetrictype
            '''
            result = self._values.get("predefined_metric_type")
            assert result is not None, "Required property 'predefined_metric_type' is missing"
            return typing.cast(builtins.str, result)

        @builtins.property
        def resource_label(self) -> typing.Optional[builtins.str]:
            '''``CfnScalingPolicy.PredefinedMetricSpecificationProperty.ResourceLabel``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-predefinedmetricspecification.html#cfn-applicationautoscaling-scalingpolicy-predefinedmetricspecification-resourcelabel
            '''
            result = self._values.get("resource_label")
            return typing.cast(typing.Optional[builtins.str], result)

        def __eq__(self, rhs: typing.Any) -> builtins.bool:
            return isinstance(rhs, self.__class__) and rhs._values == self._values

        def __ne__(self, rhs: typing.Any) -> builtins.bool:
            return not (rhs == self)

        def __repr__(self) -> str:
            return "PredefinedMetricSpecificationProperty(%s)" % ", ".join(
                k + "=" + repr(v) for k, v in self._values.items()
            )

    @jsii.data_type(
        jsii_type="@aws-cdk/aws-applicationautoscaling.CfnScalingPolicy.StepAdjustmentProperty",
        jsii_struct_bases=[],
        name_mapping={
            "metric_interval_lower_bound": "metricIntervalLowerBound",
            "metric_interval_upper_bound": "metricIntervalUpperBound",
            "scaling_adjustment": "scalingAdjustment",
        },
    )
    class StepAdjustmentProperty:
        def __init__(
            self,
            *,
            metric_interval_lower_bound: typing.Optional[jsii.Number] = None,
            metric_interval_upper_bound: typing.Optional[jsii.Number] = None,
            scaling_adjustment: jsii.Number,
        ) -> None:
            '''
            :param metric_interval_lower_bound: ``CfnScalingPolicy.StepAdjustmentProperty.MetricIntervalLowerBound``.
            :param metric_interval_upper_bound: ``CfnScalingPolicy.StepAdjustmentProperty.MetricIntervalUpperBound``.
            :param scaling_adjustment: ``CfnScalingPolicy.StepAdjustmentProperty.ScalingAdjustment``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-stepscalingpolicyconfiguration-stepadjustment.html

            Example::

                # The code below shows an example of how to instantiate this type.
                # The values are placeholders you should change.
                import aws_cdk.aws_applicationautoscaling as appscaling
                
                step_adjustment_property = appscaling.CfnScalingPolicy.StepAdjustmentProperty(
                    scaling_adjustment=123,
                
                    # the properties below are optional
                    metric_interval_lower_bound=123,
                    metric_interval_upper_bound=123
                )
            '''
            self._values: typing.Dict[str, typing.Any] = {
                "scaling_adjustment": scaling_adjustment,
            }
            if metric_interval_lower_bound is not None:
                self._values["metric_interval_lower_bound"] = metric_interval_lower_bound
            if metric_interval_upper_bound is not None:
                self._values["metric_interval_upper_bound"] = metric_interval_upper_bound

        @builtins.property
        def metric_interval_lower_bound(self) -> typing.Optional[jsii.Number]:
            '''``CfnScalingPolicy.StepAdjustmentProperty.MetricIntervalLowerBound``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-stepscalingpolicyconfiguration-stepadjustment.html#cfn-applicationautoscaling-scalingpolicy-stepscalingpolicyconfiguration-stepadjustment-metricintervallowerbound
            '''
            result = self._values.get("metric_interval_lower_bound")
            return typing.cast(typing.Optional[jsii.Number], result)

        @builtins.property
        def metric_interval_upper_bound(self) -> typing.Optional[jsii.Number]:
            '''``CfnScalingPolicy.StepAdjustmentProperty.MetricIntervalUpperBound``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-stepscalingpolicyconfiguration-stepadjustment.html#cfn-applicationautoscaling-scalingpolicy-stepscalingpolicyconfiguration-stepadjustment-metricintervalupperbound
            '''
            result = self._values.get("metric_interval_upper_bound")
            return typing.cast(typing.Optional[jsii.Number], result)

        @builtins.property
        def scaling_adjustment(self) -> jsii.Number:
            '''``CfnScalingPolicy.StepAdjustmentProperty.ScalingAdjustment``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-stepscalingpolicyconfiguration-stepadjustment.html#cfn-applicationautoscaling-scalingpolicy-stepscalingpolicyconfiguration-stepadjustment-scalingadjustment
            '''
            result = self._values.get("scaling_adjustment")
            assert result is not None, "Required property 'scaling_adjustment' is missing"
            return typing.cast(jsii.Number, result)

        def __eq__(self, rhs: typing.Any) -> builtins.bool:
            return isinstance(rhs, self.__class__) and rhs._values == self._values

        def __ne__(self, rhs: typing.Any) -> builtins.bool:
            return not (rhs == self)

        def __repr__(self) -> str:
            return "StepAdjustmentProperty(%s)" % ", ".join(
                k + "=" + repr(v) for k, v in self._values.items()
            )

    @jsii.data_type(
        jsii_type="@aws-cdk/aws-applicationautoscaling.CfnScalingPolicy.StepScalingPolicyConfigurationProperty",
        jsii_struct_bases=[],
        name_mapping={
            "adjustment_type": "adjustmentType",
            "cooldown": "cooldown",
            "metric_aggregation_type": "metricAggregationType",
            "min_adjustment_magnitude": "minAdjustmentMagnitude",
            "step_adjustments": "stepAdjustments",
        },
    )
    class StepScalingPolicyConfigurationProperty:
        def __init__(
            self,
            *,
            adjustment_type: typing.Optional[builtins.str] = None,
            cooldown: typing.Optional[jsii.Number] = None,
            metric_aggregation_type: typing.Optional[builtins.str] = None,
            min_adjustment_magnitude: typing.Optional[jsii.Number] = None,
            step_adjustments: typing.Optional[typing.Union[aws_cdk.core.IResolvable, typing.Sequence[typing.Union[aws_cdk.core.IResolvable, "CfnScalingPolicy.StepAdjustmentProperty"]]]] = None,
        ) -> None:
            '''
            :param adjustment_type: ``CfnScalingPolicy.StepScalingPolicyConfigurationProperty.AdjustmentType``.
            :param cooldown: ``CfnScalingPolicy.StepScalingPolicyConfigurationProperty.Cooldown``.
            :param metric_aggregation_type: ``CfnScalingPolicy.StepScalingPolicyConfigurationProperty.MetricAggregationType``.
            :param min_adjustment_magnitude: ``CfnScalingPolicy.StepScalingPolicyConfigurationProperty.MinAdjustmentMagnitude``.
            :param step_adjustments: ``CfnScalingPolicy.StepScalingPolicyConfigurationProperty.StepAdjustments``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-stepscalingpolicyconfiguration.html

            Example::

                # The code below shows an example of how to instantiate this type.
                # The values are placeholders you should change.
                import aws_cdk.aws_applicationautoscaling as appscaling
                
                step_scaling_policy_configuration_property = appscaling.CfnScalingPolicy.StepScalingPolicyConfigurationProperty(
                    adjustment_type="adjustmentType",
                    cooldown=123,
                    metric_aggregation_type="metricAggregationType",
                    min_adjustment_magnitude=123,
                    step_adjustments=[appscaling.CfnScalingPolicy.StepAdjustmentProperty(
                        scaling_adjustment=123,
                
                        # the properties below are optional
                        metric_interval_lower_bound=123,
                        metric_interval_upper_bound=123
                    )]
                )
            '''
            self._values: typing.Dict[str, typing.Any] = {}
            if adjustment_type is not None:
                self._values["adjustment_type"] = adjustment_type
            if cooldown is not None:
                self._values["cooldown"] = cooldown
            if metric_aggregation_type is not None:
                self._values["metric_aggregation_type"] = metric_aggregation_type
            if min_adjustment_magnitude is not None:
                self._values["min_adjustment_magnitude"] = min_adjustment_magnitude
            if step_adjustments is not None:
                self._values["step_adjustments"] = step_adjustments

        @builtins.property
        def adjustment_type(self) -> typing.Optional[builtins.str]:
            '''``CfnScalingPolicy.StepScalingPolicyConfigurationProperty.AdjustmentType``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-stepscalingpolicyconfiguration.html#cfn-applicationautoscaling-scalingpolicy-stepscalingpolicyconfiguration-adjustmenttype
            '''
            result = self._values.get("adjustment_type")
            return typing.cast(typing.Optional[builtins.str], result)

        @builtins.property
        def cooldown(self) -> typing.Optional[jsii.Number]:
            '''``CfnScalingPolicy.StepScalingPolicyConfigurationProperty.Cooldown``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-stepscalingpolicyconfiguration.html#cfn-applicationautoscaling-scalingpolicy-stepscalingpolicyconfiguration-cooldown
            '''
            result = self._values.get("cooldown")
            return typing.cast(typing.Optional[jsii.Number], result)

        @builtins.property
        def metric_aggregation_type(self) -> typing.Optional[builtins.str]:
            '''``CfnScalingPolicy.StepScalingPolicyConfigurationProperty.MetricAggregationType``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-stepscalingpolicyconfiguration.html#cfn-applicationautoscaling-scalingpolicy-stepscalingpolicyconfiguration-metricaggregationtype
            '''
            result = self._values.get("metric_aggregation_type")
            return typing.cast(typing.Optional[builtins.str], result)

        @builtins.property
        def min_adjustment_magnitude(self) -> typing.Optional[jsii.Number]:
            '''``CfnScalingPolicy.StepScalingPolicyConfigurationProperty.MinAdjustmentMagnitude``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-stepscalingpolicyconfiguration.html#cfn-applicationautoscaling-scalingpolicy-stepscalingpolicyconfiguration-minadjustmentmagnitude
            '''
            result = self._values.get("min_adjustment_magnitude")
            return typing.cast(typing.Optional[jsii.Number], result)

        @builtins.property
        def step_adjustments(
            self,
        ) -> typing.Optional[typing.Union[aws_cdk.core.IResolvable, typing.List[typing.Union[aws_cdk.core.IResolvable, "CfnScalingPolicy.StepAdjustmentProperty"]]]]:
            '''``CfnScalingPolicy.StepScalingPolicyConfigurationProperty.StepAdjustments``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-stepscalingpolicyconfiguration.html#cfn-applicationautoscaling-scalingpolicy-stepscalingpolicyconfiguration-stepadjustments
            '''
            result = self._values.get("step_adjustments")
            return typing.cast(typing.Optional[typing.Union[aws_cdk.core.IResolvable, typing.List[typing.Union[aws_cdk.core.IResolvable, "CfnScalingPolicy.StepAdjustmentProperty"]]]], result)

        def __eq__(self, rhs: typing.Any) -> builtins.bool:
            return isinstance(rhs, self.__class__) and rhs._values == self._values

        def __ne__(self, rhs: typing.Any) -> builtins.bool:
            return not (rhs == self)

        def __repr__(self) -> str:
            return "StepScalingPolicyConfigurationProperty(%s)" % ", ".join(
                k + "=" + repr(v) for k, v in self._values.items()
            )

    @jsii.data_type(
        jsii_type="@aws-cdk/aws-applicationautoscaling.CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty",
        jsii_struct_bases=[],
        name_mapping={
            "customized_metric_specification": "customizedMetricSpecification",
            "disable_scale_in": "disableScaleIn",
            "predefined_metric_specification": "predefinedMetricSpecification",
            "scale_in_cooldown": "scaleInCooldown",
            "scale_out_cooldown": "scaleOutCooldown",
            "target_value": "targetValue",
        },
    )
    class TargetTrackingScalingPolicyConfigurationProperty:
        def __init__(
            self,
            *,
            customized_metric_specification: typing.Optional[typing.Union[aws_cdk.core.IResolvable, "CfnScalingPolicy.CustomizedMetricSpecificationProperty"]] = None,
            disable_scale_in: typing.Optional[typing.Union[builtins.bool, aws_cdk.core.IResolvable]] = None,
            predefined_metric_specification: typing.Optional[typing.Union[aws_cdk.core.IResolvable, "CfnScalingPolicy.PredefinedMetricSpecificationProperty"]] = None,
            scale_in_cooldown: typing.Optional[jsii.Number] = None,
            scale_out_cooldown: typing.Optional[jsii.Number] = None,
            target_value: jsii.Number,
        ) -> None:
            '''
            :param customized_metric_specification: ``CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty.CustomizedMetricSpecification``.
            :param disable_scale_in: ``CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty.DisableScaleIn``.
            :param predefined_metric_specification: ``CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty.PredefinedMetricSpecification``.
            :param scale_in_cooldown: ``CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty.ScaleInCooldown``.
            :param scale_out_cooldown: ``CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty.ScaleOutCooldown``.
            :param target_value: ``CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty.TargetValue``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-targettrackingscalingpolicyconfiguration.html

            Example::

                # The code below shows an example of how to instantiate this type.
                # The values are placeholders you should change.
                import aws_cdk.aws_applicationautoscaling as appscaling
                
                target_tracking_scaling_policy_configuration_property = appscaling.CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty(
                    target_value=123,
                
                    # the properties below are optional
                    customized_metric_specification=appscaling.CfnScalingPolicy.CustomizedMetricSpecificationProperty(
                        metric_name="metricName",
                        namespace="namespace",
                        statistic="statistic",
                
                        # the properties below are optional
                        dimensions=[appscaling.CfnScalingPolicy.MetricDimensionProperty(
                            name="name",
                            value="value"
                        )],
                        unit="unit"
                    ),
                    disable_scale_in=False,
                    predefined_metric_specification=appscaling.CfnScalingPolicy.PredefinedMetricSpecificationProperty(
                        predefined_metric_type="predefinedMetricType",
                
                        # the properties below are optional
                        resource_label="resourceLabel"
                    ),
                    scale_in_cooldown=123,
                    scale_out_cooldown=123
                )
            '''
            self._values: typing.Dict[str, typing.Any] = {
                "target_value": target_value,
            }
            if customized_metric_specification is not None:
                self._values["customized_metric_specification"] = customized_metric_specification
            if disable_scale_in is not None:
                self._values["disable_scale_in"] = disable_scale_in
            if predefined_metric_specification is not None:
                self._values["predefined_metric_specification"] = predefined_metric_specification
            if scale_in_cooldown is not None:
                self._values["scale_in_cooldown"] = scale_in_cooldown
            if scale_out_cooldown is not None:
                self._values["scale_out_cooldown"] = scale_out_cooldown

        @builtins.property
        def customized_metric_specification(
            self,
        ) -> typing.Optional[typing.Union[aws_cdk.core.IResolvable, "CfnScalingPolicy.CustomizedMetricSpecificationProperty"]]:
            '''``CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty.CustomizedMetricSpecification``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-targettrackingscalingpolicyconfiguration.html#cfn-applicationautoscaling-scalingpolicy-targettrackingscalingpolicyconfiguration-customizedmetricspecification
            '''
            result = self._values.get("customized_metric_specification")
            return typing.cast(typing.Optional[typing.Union[aws_cdk.core.IResolvable, "CfnScalingPolicy.CustomizedMetricSpecificationProperty"]], result)

        @builtins.property
        def disable_scale_in(
            self,
        ) -> typing.Optional[typing.Union[builtins.bool, aws_cdk.core.IResolvable]]:
            '''``CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty.DisableScaleIn``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-targettrackingscalingpolicyconfiguration.html#cfn-applicationautoscaling-scalingpolicy-targettrackingscalingpolicyconfiguration-disablescalein
            '''
            result = self._values.get("disable_scale_in")
            return typing.cast(typing.Optional[typing.Union[builtins.bool, aws_cdk.core.IResolvable]], result)

        @builtins.property
        def predefined_metric_specification(
            self,
        ) -> typing.Optional[typing.Union[aws_cdk.core.IResolvable, "CfnScalingPolicy.PredefinedMetricSpecificationProperty"]]:
            '''``CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty.PredefinedMetricSpecification``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-targettrackingscalingpolicyconfiguration.html#cfn-applicationautoscaling-scalingpolicy-targettrackingscalingpolicyconfiguration-predefinedmetricspecification
            '''
            result = self._values.get("predefined_metric_specification")
            return typing.cast(typing.Optional[typing.Union[aws_cdk.core.IResolvable, "CfnScalingPolicy.PredefinedMetricSpecificationProperty"]], result)

        @builtins.property
        def scale_in_cooldown(self) -> typing.Optional[jsii.Number]:
            '''``CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty.ScaleInCooldown``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-targettrackingscalingpolicyconfiguration.html#cfn-applicationautoscaling-scalingpolicy-targettrackingscalingpolicyconfiguration-scaleincooldown
            '''
            result = self._values.get("scale_in_cooldown")
            return typing.cast(typing.Optional[jsii.Number], result)

        @builtins.property
        def scale_out_cooldown(self) -> typing.Optional[jsii.Number]:
            '''``CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty.ScaleOutCooldown``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-targettrackingscalingpolicyconfiguration.html#cfn-applicationautoscaling-scalingpolicy-targettrackingscalingpolicyconfiguration-scaleoutcooldown
            '''
            result = self._values.get("scale_out_cooldown")
            return typing.cast(typing.Optional[jsii.Number], result)

        @builtins.property
        def target_value(self) -> jsii.Number:
            '''``CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty.TargetValue``.

            :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-applicationautoscaling-scalingpolicy-targettrackingscalingpolicyconfiguration.html#cfn-applicationautoscaling-scalingpolicy-targettrackingscalingpolicyconfiguration-targetvalue
            '''
            result = self._values.get("target_value")
            assert result is not None, "Required property 'target_value' is missing"
            return typing.cast(jsii.Number, result)

        def __eq__(self, rhs: typing.Any) -> builtins.bool:
            return isinstance(rhs, self.__class__) and rhs._values == self._values

        def __ne__(self, rhs: typing.Any) -> builtins.bool:
            return not (rhs == self)

        def __repr__(self) -> str:
            return "TargetTrackingScalingPolicyConfigurationProperty(%s)" % ", ".join(
                k + "=" + repr(v) for k, v in self._values.items()
            )


@jsii.data_type(
    jsii_type="@aws-cdk/aws-applicationautoscaling.CfnScalingPolicyProps",
    jsii_struct_bases=[],
    name_mapping={
        "policy_name": "policyName",
        "policy_type": "policyType",
        "resource_id": "resourceId",
        "scalable_dimension": "scalableDimension",
        "scaling_target_id": "scalingTargetId",
        "service_namespace": "serviceNamespace",
        "step_scaling_policy_configuration": "stepScalingPolicyConfiguration",
        "target_tracking_scaling_policy_configuration": "targetTrackingScalingPolicyConfiguration",
    },
)
class CfnScalingPolicyProps:
    def __init__(
        self,
        *,
        policy_name: builtins.str,
        policy_type: builtins.str,
        resource_id: typing.Optional[builtins.str] = None,
        scalable_dimension: typing.Optional[builtins.str] = None,
        scaling_target_id: typing.Optional[builtins.str] = None,
        service_namespace: typing.Optional[builtins.str] = None,
        step_scaling_policy_configuration: typing.Optional[typing.Union[aws_cdk.core.IResolvable, CfnScalingPolicy.StepScalingPolicyConfigurationProperty]] = None,
        target_tracking_scaling_policy_configuration: typing.Optional[typing.Union[aws_cdk.core.IResolvable, CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty]] = None,
    ) -> None:
        '''Properties for defining a ``AWS::ApplicationAutoScaling::ScalingPolicy``.

        :param policy_name: ``AWS::ApplicationAutoScaling::ScalingPolicy.PolicyName``.
        :param policy_type: ``AWS::ApplicationAutoScaling::ScalingPolicy.PolicyType``.
        :param resource_id: ``AWS::ApplicationAutoScaling::ScalingPolicy.ResourceId``.
        :param scalable_dimension: ``AWS::ApplicationAutoScaling::ScalingPolicy.ScalableDimension``.
        :param scaling_target_id: ``AWS::ApplicationAutoScaling::ScalingPolicy.ScalingTargetId``.
        :param service_namespace: ``AWS::ApplicationAutoScaling::ScalingPolicy.ServiceNamespace``.
        :param step_scaling_policy_configuration: ``AWS::ApplicationAutoScaling::ScalingPolicy.StepScalingPolicyConfiguration``.
        :param target_tracking_scaling_policy_configuration: ``AWS::ApplicationAutoScaling::ScalingPolicy.TargetTrackingScalingPolicyConfiguration``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalingpolicy.html

        Example::

            # The code below shows an example of how to instantiate this type.
            # The values are placeholders you should change.
            import aws_cdk.aws_applicationautoscaling as appscaling
            
            cfn_scaling_policy_props = appscaling.CfnScalingPolicyProps(
                policy_name="policyName",
                policy_type="policyType",
            
                # the properties below are optional
                resource_id="resourceId",
                scalable_dimension="scalableDimension",
                scaling_target_id="scalingTargetId",
                service_namespace="serviceNamespace",
                step_scaling_policy_configuration=appscaling.CfnScalingPolicy.StepScalingPolicyConfigurationProperty(
                    adjustment_type="adjustmentType",
                    cooldown=123,
                    metric_aggregation_type="metricAggregationType",
                    min_adjustment_magnitude=123,
                    step_adjustments=[appscaling.CfnScalingPolicy.StepAdjustmentProperty(
                        scaling_adjustment=123,
            
                        # the properties below are optional
                        metric_interval_lower_bound=123,
                        metric_interval_upper_bound=123
                    )]
                ),
                target_tracking_scaling_policy_configuration=appscaling.CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty(
                    target_value=123,
            
                    # the properties below are optional
                    customized_metric_specification=appscaling.CfnScalingPolicy.CustomizedMetricSpecificationProperty(
                        metric_name="metricName",
                        namespace="namespace",
                        statistic="statistic",
            
                        # the properties below are optional
                        dimensions=[appscaling.CfnScalingPolicy.MetricDimensionProperty(
                            name="name",
                            value="value"
                        )],
                        unit="unit"
                    ),
                    disable_scale_in=False,
                    predefined_metric_specification=appscaling.CfnScalingPolicy.PredefinedMetricSpecificationProperty(
                        predefined_metric_type="predefinedMetricType",
            
                        # the properties below are optional
                        resource_label="resourceLabel"
                    ),
                    scale_in_cooldown=123,
                    scale_out_cooldown=123
                )
            )
        '''
        self._values: typing.Dict[str, typing.Any] = {
            "policy_name": policy_name,
            "policy_type": policy_type,
        }
        if resource_id is not None:
            self._values["resource_id"] = resource_id
        if scalable_dimension is not None:
            self._values["scalable_dimension"] = scalable_dimension
        if scaling_target_id is not None:
            self._values["scaling_target_id"] = scaling_target_id
        if service_namespace is not None:
            self._values["service_namespace"] = service_namespace
        if step_scaling_policy_configuration is not None:
            self._values["step_scaling_policy_configuration"] = step_scaling_policy_configuration
        if target_tracking_scaling_policy_configuration is not None:
            self._values["target_tracking_scaling_policy_configuration"] = target_tracking_scaling_policy_configuration

    @builtins.property
    def policy_name(self) -> builtins.str:
        '''``AWS::ApplicationAutoScaling::ScalingPolicy.PolicyName``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalingpolicy.html#cfn-applicationautoscaling-scalingpolicy-policyname
        '''
        result = self._values.get("policy_name")
        assert result is not None, "Required property 'policy_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def policy_type(self) -> builtins.str:
        '''``AWS::ApplicationAutoScaling::ScalingPolicy.PolicyType``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalingpolicy.html#cfn-applicationautoscaling-scalingpolicy-policytype
        '''
        result = self._values.get("policy_type")
        assert result is not None, "Required property 'policy_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def resource_id(self) -> typing.Optional[builtins.str]:
        '''``AWS::ApplicationAutoScaling::ScalingPolicy.ResourceId``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalingpolicy.html#cfn-applicationautoscaling-scalingpolicy-resourceid
        '''
        result = self._values.get("resource_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def scalable_dimension(self) -> typing.Optional[builtins.str]:
        '''``AWS::ApplicationAutoScaling::ScalingPolicy.ScalableDimension``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalingpolicy.html#cfn-applicationautoscaling-scalingpolicy-scalabledimension
        '''
        result = self._values.get("scalable_dimension")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def scaling_target_id(self) -> typing.Optional[builtins.str]:
        '''``AWS::ApplicationAutoScaling::ScalingPolicy.ScalingTargetId``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalingpolicy.html#cfn-applicationautoscaling-scalingpolicy-scalingtargetid
        '''
        result = self._values.get("scaling_target_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def service_namespace(self) -> typing.Optional[builtins.str]:
        '''``AWS::ApplicationAutoScaling::ScalingPolicy.ServiceNamespace``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalingpolicy.html#cfn-applicationautoscaling-scalingpolicy-servicenamespace
        '''
        result = self._values.get("service_namespace")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def step_scaling_policy_configuration(
        self,
    ) -> typing.Optional[typing.Union[aws_cdk.core.IResolvable, CfnScalingPolicy.StepScalingPolicyConfigurationProperty]]:
        '''``AWS::ApplicationAutoScaling::ScalingPolicy.StepScalingPolicyConfiguration``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalingpolicy.html#cfn-applicationautoscaling-scalingpolicy-stepscalingpolicyconfiguration
        '''
        result = self._values.get("step_scaling_policy_configuration")
        return typing.cast(typing.Optional[typing.Union[aws_cdk.core.IResolvable, CfnScalingPolicy.StepScalingPolicyConfigurationProperty]], result)

    @builtins.property
    def target_tracking_scaling_policy_configuration(
        self,
    ) -> typing.Optional[typing.Union[aws_cdk.core.IResolvable, CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty]]:
        '''``AWS::ApplicationAutoScaling::ScalingPolicy.TargetTrackingScalingPolicyConfiguration``.

        :link: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-applicationautoscaling-scalingpolicy.html#cfn-applicationautoscaling-scalingpolicy-targettrackingscalingpolicyconfiguration
        '''
        result = self._values.get("target_tracking_scaling_policy_configuration")
        return typing.cast(typing.Optional[typing.Union[aws_cdk.core.IResolvable, CfnScalingPolicy.TargetTrackingScalingPolicyConfigurationProperty]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CfnScalingPolicyProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk/aws-applicationautoscaling.CronOptions",
    jsii_struct_bases=[],
    name_mapping={
        "day": "day",
        "hour": "hour",
        "minute": "minute",
        "month": "month",
        "week_day": "weekDay",
        "year": "year",
    },
)
class CronOptions:
    def __init__(
        self,
        *,
        day: typing.Optional[builtins.str] = None,
        hour: typing.Optional[builtins.str] = None,
        minute: typing.Optional[builtins.str] = None,
        month: typing.Optional[builtins.str] = None,
        week_day: typing.Optional[builtins.str] = None,
        year: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Options to configure a cron expression.

        All fields are strings so you can use complex expressions. Absence of
        a field implies '*' or '?', whichever one is appropriate.

        :param day: The day of the month to run this rule at. Default: - Every day of the month
        :param hour: The hour to run this rule at. Default: - Every hour
        :param minute: The minute to run this rule at. Default: - Every minute
        :param month: The month to run this rule at. Default: - Every month
        :param week_day: The day of the week to run this rule at. Default: - Any day of the week
        :param year: The year to run this rule at. Default: - Every year

        :see: https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html#CronExpressions

        Example::

            # cluster is of type Cluster
            
            load_balanced_fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(self, "Service",
                cluster=cluster,
                memory_limit_mi_b=1024,
                desired_count=1,
                cpu=512,
                task_image_options=ecsPatterns.ApplicationLoadBalancedTaskImageOptions(
                    image=ecs.ContainerImage.from_registry("amazon/amazon-ecs-sample")
                )
            )
            
            scalable_target = load_balanced_fargate_service.service.auto_scale_task_count(
                min_capacity=5,
                max_capacity=20
            )
            
            scalable_target.scale_on_schedule("DaytimeScaleDown",
                schedule=appscaling.Schedule.cron(hour="8", minute="0"),
                min_capacity=1
            )
            
            scalable_target.scale_on_schedule("EveningRushScaleUp",
                schedule=appscaling.Schedule.cron(hour="20", minute="0"),
                min_capacity=10
            )
        '''
        self._values: typing.Dict[str, typing.Any] = {}
        if day is not None:
            self._values["day"] = day
        if hour is not None:
            self._values["hour"] = hour
        if minute is not None:
            self._values["minute"] = minute
        if month is not None:
            self._values["month"] = month
        if week_day is not None:
            self._values["week_day"] = week_day
        if year is not None:
            self._values["year"] = year

    @builtins.property
    def day(self) -> typing.Optional[builtins.str]:
        '''The day of the month to run this rule at.

        :default: - Every day of the month
        '''
        result = self._values.get("day")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def hour(self) -> typing.Optional[builtins.str]:
        '''The hour to run this rule at.

        :default: - Every hour
        '''
        result = self._values.get("hour")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def minute(self) -> typing.Optional[builtins.str]:
        '''The minute to run this rule at.

        :default: - Every minute
        '''
        result = self._values.get("minute")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def month(self) -> typing.Optional[builtins.str]:
        '''The month to run this rule at.

        :default: - Every month
        '''
        result = self._values.get("month")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def week_day(self) -> typing.Optional[builtins.str]:
        '''The day of the week to run this rule at.

        :default: - Any day of the week
        '''
        result = self._values.get("week_day")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def year(self) -> typing.Optional[builtins.str]:
        '''The year to run this rule at.

        :default: - Every year
        '''
        result = self._values.get("year")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CronOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk/aws-applicationautoscaling.EnableScalingProps",
    jsii_struct_bases=[],
    name_mapping={"max_capacity": "maxCapacity", "min_capacity": "minCapacity"},
)
class EnableScalingProps:
    def __init__(
        self,
        *,
        max_capacity: jsii.Number,
        min_capacity: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''Properties for enabling Application Auto Scaling.

        :param max_capacity: Maximum capacity to scale to.
        :param min_capacity: Minimum capacity to scale to. Default: 1

        Example::

            # cluster is of type Cluster
            
            load_balanced_fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(self, "Service",
                cluster=cluster,
                memory_limit_mi_b=1024,
                desired_count=1,
                cpu=512,
                task_image_options=ecsPatterns.ApplicationLoadBalancedTaskImageOptions(
                    image=ecs.ContainerImage.from_registry("amazon/amazon-ecs-sample")
                )
            )
            
            scalable_target = load_balanced_fargate_service.service.auto_scale_task_count(
                min_capacity=1,
                max_capacity=20
            )
            
            scalable_target.scale_on_cpu_utilization("CpuScaling",
                target_utilization_percent=50
            )
            
            scalable_target.scale_on_memory_utilization("MemoryScaling",
                target_utilization_percent=50
            )
        '''
        self._values: typing.Dict[str, typing.Any] = {
            "max_capacity": max_capacity,
        }
        if min_capacity is not None:
            self._values["min_capacity"] = min_capacity

    @builtins.property
    def max_capacity(self) -> jsii.Number:
        '''Maximum capacity to scale to.'''
        result = self._values.get("max_capacity")
        assert result is not None, "Required property 'max_capacity' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def min_capacity(self) -> typing.Optional[jsii.Number]:
        '''Minimum capacity to scale to.

        :default: 1
        '''
        result = self._values.get("min_capacity")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "EnableScalingProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.interface(jsii_type="@aws-cdk/aws-applicationautoscaling.IScalableTarget")
class IScalableTarget(aws_cdk.core.IResource, typing_extensions.Protocol):
    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="scalableTargetId")
    def scalable_target_id(self) -> builtins.str:
        '''
        :attribute: true
        '''
        ...


class _IScalableTargetProxy(
    jsii.proxy_for(aws_cdk.core.IResource) # type: ignore[misc]
):
    __jsii_type__: typing.ClassVar[str] = "@aws-cdk/aws-applicationautoscaling.IScalableTarget"

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="scalableTargetId")
    def scalable_target_id(self) -> builtins.str:
        '''
        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "scalableTargetId"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IScalableTarget).__jsii_proxy_class__ = lambda : _IScalableTargetProxy


@jsii.enum(jsii_type="@aws-cdk/aws-applicationautoscaling.MetricAggregationType")
class MetricAggregationType(enum.Enum):
    '''How the scaling metric is going to be aggregated.'''

    AVERAGE = "AVERAGE"
    '''Average.'''
    MAXIMUM = "MAXIMUM"
    '''Maximum.'''
    MINIMUM = "MINIMUM"
    '''Minimum.'''


@jsii.enum(jsii_type="@aws-cdk/aws-applicationautoscaling.PredefinedMetric")
class PredefinedMetric(enum.Enum):
    '''One of the predefined autoscaling metrics.

    Example::

        import aws_cdk.aws_lambda as lambda_
        
        # code is of type Code
        
        
        handler = lambda_.Function(self, "MyFunction",
            runtime=lambda_.Runtime.PYTHON_3_7,
            handler="index.handler",
            code=code,
        
            reserved_concurrent_executions=2
        )
        
        fn_ver = handler.add_version("CDKLambdaVersion", undefined, "demo alias", 10)
        
        target = appscaling.ScalableTarget(self, "ScalableTarget",
            service_namespace=appscaling.ServiceNamespace.LAMBDA,
            max_capacity=100,
            min_capacity=10,
            resource_id=f"function:{handler.functionName}:{fnVer.version}",
            scalable_dimension="lambda:function:ProvisionedConcurrency"
        )
        
        target.scale_to_track_metric("PceTracking",
            target_value=0.9,
            predefined_metric=appscaling.PredefinedMetric.LAMBDA_PROVISIONED_CONCURRENCY_UTILIZATION
        )
    '''

    ALB_REQUEST_COUNT_PER_TARGET = "ALB_REQUEST_COUNT_PER_TARGET"
    '''ALB_REQUEST_COUNT_PER_TARGET.

    :see: https://docs.aws.amazon.com/autoscaling/application/APIReference/API_PredefinedMetricSpecification.html
    '''
    DYANMODB_WRITE_CAPACITY_UTILIZATION = "DYANMODB_WRITE_CAPACITY_UTILIZATION"
    '''DYANMODB_WRITE_CAPACITY_UTILIZATION.

    :see: https://docs.aws.amazon.com/autoscaling/application/APIReference/API_PredefinedMetricSpecification.html
    '''
    DYNAMODB_READ_CAPACITY_UTILIZATION = "DYNAMODB_READ_CAPACITY_UTILIZATION"
    '''DYNAMODB_READ_CAPACITY_UTILIZATIO.

    :see: https://docs.aws.amazon.com/autoscaling/application/APIReference/API_PredefinedMetricSpecification.html
    '''
    EC2_SPOT_FLEET_REQUEST_AVERAGE_CPU_UTILIZATION = "EC2_SPOT_FLEET_REQUEST_AVERAGE_CPU_UTILIZATION"
    '''EC2_SPOT_FLEET_REQUEST_AVERAGE_CPU_UTILIZATION.

    :see: https://docs.aws.amazon.com/autoscaling/application/APIReference/API_PredefinedMetricSpecification.html
    '''
    EC2_SPOT_FLEET_REQUEST_AVERAGE_NETWORK_IN = "EC2_SPOT_FLEET_REQUEST_AVERAGE_NETWORK_IN"
    '''EC2_SPOT_FLEET_REQUEST_AVERAGE_NETWORK_IN.

    :see: https://docs.aws.amazon.com/autoscaling/application/APIReference/API_PredefinedMetricSpecification.html
    '''
    EC2_SPOT_FLEET_REQUEST_AVERAGE_NETWORK_OUT = "EC2_SPOT_FLEET_REQUEST_AVERAGE_NETWORK_OUT"
    '''EC2_SPOT_FLEET_REQUEST_AVERAGE_NETWORK_OUT.

    :see: https://docs.aws.amazon.com/autoscaling/application/APIReference/API_PredefinedMetricSpecification.html
    '''
    ECS_SERVICE_AVERAGE_CPU_UTILIZATION = "ECS_SERVICE_AVERAGE_CPU_UTILIZATION"
    '''ECS_SERVICE_AVERAGE_CPU_UTILIZATION.

    :see: https://docs.aws.amazon.com/autoscaling/application/APIReference/API_PredefinedMetricSpecification.html
    '''
    ECS_SERVICE_AVERAGE_MEMORY_UTILIZATION = "ECS_SERVICE_AVERAGE_MEMORY_UTILIZATION"
    '''ECS_SERVICE_AVERAGE_MEMORY_UTILIZATION.

    :see: https://docs.aws.amazon.com/autoscaling/application/APIReference/API_PredefinedMetricSpecification.html
    '''
    KAFKA_BROKER_STORAGE_UTILIZATION = "KAFKA_BROKER_STORAGE_UTILIZATION"
    '''KAFKA_BROKER_STORAGE_UTILIZATION.

    :see: https://docs.aws.amazon.com/autoscaling/application/APIReference/API_PredefinedMetricSpecification.html
    '''
    LAMBDA_PROVISIONED_CONCURRENCY_UTILIZATION = "LAMBDA_PROVISIONED_CONCURRENCY_UTILIZATION"
    '''LAMBDA_PROVISIONED_CONCURRENCY_UTILIZATION.

    :see: https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics.html#monitoring-metrics-concurrency
    '''
    RDS_READER_AVERAGE_CPU_UTILIZATION = "RDS_READER_AVERAGE_CPU_UTILIZATION"
    '''RDS_READER_AVERAGE_CPU_UTILIZATION.

    :see: https://docs.aws.amazon.com/autoscaling/application/APIReference/API_PredefinedMetricSpecification.html
    '''
    RDS_READER_AVERAGE_DATABASE_CONNECTIONS = "RDS_READER_AVERAGE_DATABASE_CONNECTIONS"
    '''RDS_READER_AVERAGE_DATABASE_CONNECTIONS.

    :see: https://docs.aws.amazon.com/autoscaling/application/APIReference/API_PredefinedMetricSpecification.html
    '''
    SAGEMAKER_VARIANT_INVOCATIONS_PER_INSTANCE = "SAGEMAKER_VARIANT_INVOCATIONS_PER_INSTANCE"
    '''SAGEMAKER_VARIANT_INVOCATIONS_PER_INSTANCE.

    :see: https://docs.aws.amazon.com/autoscaling/application/APIReference/API_PredefinedMetricSpecification.html
    '''


@jsii.implements(IScalableTarget)
class ScalableTarget(
    aws_cdk.core.Resource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk/aws-applicationautoscaling.ScalableTarget",
):
    '''Define a scalable target.

    Example::

        import aws_cdk.aws_lambda as lambda_
        
        # code is of type Code
        
        
        handler = lambda_.Function(self, "MyFunction",
            runtime=lambda_.Runtime.PYTHON_3_7,
            handler="index.handler",
            code=code,
        
            reserved_concurrent_executions=2
        )
        
        fn_ver = handler.add_version("CDKLambdaVersion", undefined, "demo alias", 10)
        
        target = appscaling.ScalableTarget(self, "ScalableTarget",
            service_namespace=appscaling.ServiceNamespace.LAMBDA,
            max_capacity=100,
            min_capacity=10,
            resource_id=f"function:{handler.functionName}:{fnVer.version}",
            scalable_dimension="lambda:function:ProvisionedConcurrency"
        )
        
        target.scale_to_track_metric("PceTracking",
            target_value=0.9,
            predefined_metric=appscaling.PredefinedMetric.LAMBDA_PROVISIONED_CONCURRENCY_UTILIZATION
        )
    '''

    def __init__(
        self,
        scope: constructs.Construct,
        id: builtins.str,
        *,
        max_capacity: jsii.Number,
        min_capacity: jsii.Number,
        resource_id: builtins.str,
        scalable_dimension: builtins.str,
        service_namespace: "ServiceNamespace",
        role: typing.Optional[aws_cdk.aws_iam.IRole] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param max_capacity: The maximum value that Application Auto Scaling can use to scale a target during a scaling activity.
        :param min_capacity: The minimum value that Application Auto Scaling can use to scale a target during a scaling activity.
        :param resource_id: The resource identifier to associate with this scalable target. This string consists of the resource type and unique identifier. Example value: ``service/ecsStack-MyECSCluster-AB12CDE3F4GH/ecsStack-MyECSService-AB12CDE3F4GH``
        :param scalable_dimension: The scalable dimension that's associated with the scalable target. Specify the service namespace, resource type, and scaling property. Example value: ``ecs:service:DesiredCount``
        :param service_namespace: The namespace of the AWS service that provides the resource or custom-resource for a resource provided by your own application or service. For valid AWS service namespace values, see the RegisterScalableTarget action in the Application Auto Scaling API Reference.
        :param role: Role that allows Application Auto Scaling to modify your scalable target. Default: A role is automatically created
        '''
        props = ScalableTargetProps(
            max_capacity=max_capacity,
            min_capacity=min_capacity,
            resource_id=resource_id,
            scalable_dimension=scalable_dimension,
            service_namespace=service_namespace,
            role=role,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="fromScalableTargetId") # type: ignore[misc]
    @builtins.classmethod
    def from_scalable_target_id(
        cls,
        scope: constructs.Construct,
        id: builtins.str,
        scalable_target_id: builtins.str,
    ) -> IScalableTarget:
        '''
        :param scope: -
        :param id: -
        :param scalable_target_id: -
        '''
        return typing.cast(IScalableTarget, jsii.sinvoke(cls, "fromScalableTargetId", [scope, id, scalable_target_id]))

    @jsii.member(jsii_name="addToRolePolicy")
    def add_to_role_policy(self, statement: aws_cdk.aws_iam.PolicyStatement) -> None:
        '''Add a policy statement to the role's policy.

        :param statement: -
        '''
        return typing.cast(None, jsii.invoke(self, "addToRolePolicy", [statement]))

    @jsii.member(jsii_name="scaleOnMetric")
    def scale_on_metric(
        self,
        id: builtins.str,
        *,
        adjustment_type: typing.Optional[AdjustmentType] = None,
        cooldown: typing.Optional[aws_cdk.core.Duration] = None,
        evaluation_periods: typing.Optional[jsii.Number] = None,
        metric: aws_cdk.aws_cloudwatch.IMetric,
        metric_aggregation_type: typing.Optional[MetricAggregationType] = None,
        min_adjustment_magnitude: typing.Optional[jsii.Number] = None,
        scaling_steps: typing.Sequence["ScalingInterval"],
    ) -> "StepScalingPolicy":
        '''Scale out or in, in response to a metric.

        :param id: -
        :param adjustment_type: How the adjustment numbers inside 'intervals' are interpreted. Default: ChangeInCapacity
        :param cooldown: Grace period after scaling activity. Subsequent scale outs during the cooldown period are squashed so that only the biggest scale out happens. Subsequent scale ins during the cooldown period are ignored. Default: No cooldown period
        :param evaluation_periods: How many evaluation periods of the metric to wait before triggering a scaling action. Raising this value can be used to smooth out the metric, at the expense of slower response times. Default: 1
        :param metric: Metric to scale on.
        :param metric_aggregation_type: Aggregation to apply to all data points over the evaluation periods. Only has meaning if ``evaluationPeriods != 1``. Default: - The statistic from the metric if applicable (MIN, MAX, AVERAGE), otherwise AVERAGE.
        :param min_adjustment_magnitude: Minimum absolute number to adjust capacity with as result of percentage scaling. Only when using AdjustmentType = PercentChangeInCapacity, this number controls the minimum absolute effect size. Default: No minimum scaling effect
        :param scaling_steps: The intervals for scaling. Maps a range of metric values to a particular scaling behavior.
        '''
        props = BasicStepScalingPolicyProps(
            adjustment_type=adjustment_type,
            cooldown=cooldown,
            evaluation_periods=evaluation_periods,
            metric=metric,
            metric_aggregation_type=metric_aggregation_type,
            min_adjustment_magnitude=min_adjustment_magnitude,
            scaling_steps=scaling_steps,
        )

        return typing.cast("StepScalingPolicy", jsii.invoke(self, "scaleOnMetric", [id, props]))

    @jsii.member(jsii_name="scaleOnSchedule")
    def scale_on_schedule(
        self,
        id: builtins.str,
        *,
        end_time: typing.Optional[datetime.datetime] = None,
        max_capacity: typing.Optional[jsii.Number] = None,
        min_capacity: typing.Optional[jsii.Number] = None,
        schedule: "Schedule",
        start_time: typing.Optional[datetime.datetime] = None,
    ) -> None:
        '''Scale out or in based on time.

        :param id: -
        :param end_time: When this scheduled action expires. Default: The rule never expires.
        :param max_capacity: The new maximum capacity. During the scheduled time, the current capacity is above the maximum capacity, Application Auto Scaling scales in to the maximum capacity. At least one of maxCapacity and minCapacity must be supplied. Default: No new maximum capacity
        :param min_capacity: The new minimum capacity. During the scheduled time, if the current capacity is below the minimum capacity, Application Auto Scaling scales out to the minimum capacity. At least one of maxCapacity and minCapacity must be supplied. Default: No new minimum capacity
        :param schedule: When to perform this action.
        :param start_time: When this scheduled action becomes active. Default: The rule is activate immediately
        '''
        action = ScalingSchedule(
            end_time=end_time,
            max_capacity=max_capacity,
            min_capacity=min_capacity,
            schedule=schedule,
            start_time=start_time,
        )

        return typing.cast(None, jsii.invoke(self, "scaleOnSchedule", [id, action]))

    @jsii.member(jsii_name="scaleToTrackMetric")
    def scale_to_track_metric(
        self,
        id: builtins.str,
        *,
        custom_metric: typing.Optional[aws_cdk.aws_cloudwatch.IMetric] = None,
        predefined_metric: typing.Optional[PredefinedMetric] = None,
        resource_label: typing.Optional[builtins.str] = None,
        target_value: jsii.Number,
        disable_scale_in: typing.Optional[builtins.bool] = None,
        policy_name: typing.Optional[builtins.str] = None,
        scale_in_cooldown: typing.Optional[aws_cdk.core.Duration] = None,
        scale_out_cooldown: typing.Optional[aws_cdk.core.Duration] = None,
    ) -> "TargetTrackingScalingPolicy":
        '''Scale out or in in order to keep a metric around a target value.

        :param id: -
        :param custom_metric: A custom metric for application autoscaling. The metric must track utilization. Scaling out will happen if the metric is higher than the target value, scaling in will happen in the metric is lower than the target value. Exactly one of customMetric or predefinedMetric must be specified. Default: - No custom metric.
        :param predefined_metric: A predefined metric for application autoscaling. The metric must track utilization. Scaling out will happen if the metric is higher than the target value, scaling in will happen in the metric is lower than the target value. Exactly one of customMetric or predefinedMetric must be specified. Default: - No predefined metrics.
        :param resource_label: Identify the resource associated with the metric type. Only used for predefined metric ALBRequestCountPerTarget. Example value: ``app/<load-balancer-name>/<load-balancer-id>/targetgroup/<target-group-name>/<target-group-id>`` Default: - No resource label.
        :param target_value: The target value for the metric.
        :param disable_scale_in: Indicates whether scale in by the target tracking policy is disabled. If the value is true, scale in is disabled and the target tracking policy won't remove capacity from the scalable resource. Otherwise, scale in is enabled and the target tracking policy can remove capacity from the scalable resource. Default: false
        :param policy_name: A name for the scaling policy. Default: - Automatically generated name.
        :param scale_in_cooldown: Period after a scale in activity completes before another scale in activity can start. Default: Duration.seconds(300) for the following scalable targets: ECS services, Spot Fleet requests, EMR clusters, AppStream 2.0 fleets, Aurora DB clusters, Amazon SageMaker endpoint variants, Custom resources. For all other scalable targets, the default value is Duration.seconds(0): DynamoDB tables, DynamoDB global secondary indexes, Amazon Comprehend document classification endpoints, Lambda provisioned concurrency
        :param scale_out_cooldown: Period after a scale out activity completes before another scale out activity can start. Default: Duration.seconds(300) for the following scalable targets: ECS services, Spot Fleet requests, EMR clusters, AppStream 2.0 fleets, Aurora DB clusters, Amazon SageMaker endpoint variants, Custom resources. For all other scalable targets, the default value is Duration.seconds(0): DynamoDB tables, DynamoDB global secondary indexes, Amazon Comprehend document classification endpoints, Lambda provisioned concurrency
        '''
        props = BasicTargetTrackingScalingPolicyProps(
            custom_metric=custom_metric,
            predefined_metric=predefined_metric,
            resource_label=resource_label,
            target_value=target_value,
            disable_scale_in=disable_scale_in,
            policy_name=policy_name,
            scale_in_cooldown=scale_in_cooldown,
            scale_out_cooldown=scale_out_cooldown,
        )

        return typing.cast("TargetTrackingScalingPolicy", jsii.invoke(self, "scaleToTrackMetric", [id, props]))

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="role")
    def role(self) -> aws_cdk.aws_iam.IRole:
        '''The role used to give AutoScaling permissions to your resource.'''
        return typing.cast(aws_cdk.aws_iam.IRole, jsii.get(self, "role"))

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="scalableTargetId")
    def scalable_target_id(self) -> builtins.str:
        '''ID of the Scalable Target.

        Example value: ``service/ecsStack-MyECSCluster-AB12CDE3F4GH/ecsStack-MyECSService-AB12CDE3F4GH|ecs:service:DesiredCount|ecs``

        :attribute: true
        '''
        return typing.cast(builtins.str, jsii.get(self, "scalableTargetId"))


@jsii.data_type(
    jsii_type="@aws-cdk/aws-applicationautoscaling.ScalableTargetProps",
    jsii_struct_bases=[],
    name_mapping={
        "max_capacity": "maxCapacity",
        "min_capacity": "minCapacity",
        "resource_id": "resourceId",
        "scalable_dimension": "scalableDimension",
        "service_namespace": "serviceNamespace",
        "role": "role",
    },
)
class ScalableTargetProps:
    def __init__(
        self,
        *,
        max_capacity: jsii.Number,
        min_capacity: jsii.Number,
        resource_id: builtins.str,
        scalable_dimension: builtins.str,
        service_namespace: "ServiceNamespace",
        role: typing.Optional[aws_cdk.aws_iam.IRole] = None,
    ) -> None:
        '''Properties for a scalable target.

        :param max_capacity: The maximum value that Application Auto Scaling can use to scale a target during a scaling activity.
        :param min_capacity: The minimum value that Application Auto Scaling can use to scale a target during a scaling activity.
        :param resource_id: The resource identifier to associate with this scalable target. This string consists of the resource type and unique identifier. Example value: ``service/ecsStack-MyECSCluster-AB12CDE3F4GH/ecsStack-MyECSService-AB12CDE3F4GH``
        :param scalable_dimension: The scalable dimension that's associated with the scalable target. Specify the service namespace, resource type, and scaling property. Example value: ``ecs:service:DesiredCount``
        :param service_namespace: The namespace of the AWS service that provides the resource or custom-resource for a resource provided by your own application or service. For valid AWS service namespace values, see the RegisterScalableTarget action in the Application Auto Scaling API Reference.
        :param role: Role that allows Application Auto Scaling to modify your scalable target. Default: A role is automatically created

        Example::

            import aws_cdk.aws_lambda as lambda_
            
            # code is of type Code
            
            
            handler = lambda_.Function(self, "MyFunction",
                runtime=lambda_.Runtime.PYTHON_3_7,
                handler="index.handler",
                code=code,
            
                reserved_concurrent_executions=2
            )
            
            fn_ver = handler.add_version("CDKLambdaVersion", undefined, "demo alias", 10)
            
            target = appscaling.ScalableTarget(self, "ScalableTarget",
                service_namespace=appscaling.ServiceNamespace.LAMBDA,
                max_capacity=100,
                min_capacity=10,
                resource_id=f"function:{handler.functionName}:{fnVer.version}",
                scalable_dimension="lambda:function:ProvisionedConcurrency"
            )
            
            target.scale_to_track_metric("PceTracking",
                target_value=0.9,
                predefined_metric=appscaling.PredefinedMetric.LAMBDA_PROVISIONED_CONCURRENCY_UTILIZATION
            )
        '''
        self._values: typing.Dict[str, typing.Any] = {
            "max_capacity": max_capacity,
            "min_capacity": min_capacity,
            "resource_id": resource_id,
            "scalable_dimension": scalable_dimension,
            "service_namespace": service_namespace,
        }
        if role is not None:
            self._values["role"] = role

    @builtins.property
    def max_capacity(self) -> jsii.Number:
        '''The maximum value that Application Auto Scaling can use to scale a target during a scaling activity.'''
        result = self._values.get("max_capacity")
        assert result is not None, "Required property 'max_capacity' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def min_capacity(self) -> jsii.Number:
        '''The minimum value that Application Auto Scaling can use to scale a target during a scaling activity.'''
        result = self._values.get("min_capacity")
        assert result is not None, "Required property 'min_capacity' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def resource_id(self) -> builtins.str:
        '''The resource identifier to associate with this scalable target.

        This string consists of the resource type and unique identifier.

        Example value: ``service/ecsStack-MyECSCluster-AB12CDE3F4GH/ecsStack-MyECSService-AB12CDE3F4GH``

        :see: https://docs.aws.amazon.com/autoscaling/application/APIReference/API_RegisterScalableTarget.html
        '''
        result = self._values.get("resource_id")
        assert result is not None, "Required property 'resource_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def scalable_dimension(self) -> builtins.str:
        '''The scalable dimension that's associated with the scalable target.

        Specify the service namespace, resource type, and scaling property.

        Example value: ``ecs:service:DesiredCount``

        :see: https://docs.aws.amazon.com/autoscaling/application/APIReference/API_ScalingPolicy.html
        '''
        result = self._values.get("scalable_dimension")
        assert result is not None, "Required property 'scalable_dimension' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def service_namespace(self) -> "ServiceNamespace":
        '''The namespace of the AWS service that provides the resource or custom-resource for a resource provided by your own application or service.

        For valid AWS service namespace values, see the RegisterScalableTarget
        action in the Application Auto Scaling API Reference.

        :see: https://docs.aws.amazon.com/autoscaling/application/APIReference/API_RegisterScalableTarget.html
        '''
        result = self._values.get("service_namespace")
        assert result is not None, "Required property 'service_namespace' is missing"
        return typing.cast("ServiceNamespace", result)

    @builtins.property
    def role(self) -> typing.Optional[aws_cdk.aws_iam.IRole]:
        '''Role that allows Application Auto Scaling to modify your scalable target.

        :default: A role is automatically created
        '''
        result = self._values.get("role")
        return typing.cast(typing.Optional[aws_cdk.aws_iam.IRole], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ScalableTargetProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk/aws-applicationautoscaling.ScalingInterval",
    jsii_struct_bases=[],
    name_mapping={"change": "change", "lower": "lower", "upper": "upper"},
)
class ScalingInterval:
    def __init__(
        self,
        *,
        change: jsii.Number,
        lower: typing.Optional[jsii.Number] = None,
        upper: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''A range of metric values in which to apply a certain scaling operation.

        :param change: The capacity adjustment to apply in this interval. The number is interpreted differently based on AdjustmentType: - ChangeInCapacity: add the adjustment to the current capacity. The number can be positive or negative. - PercentChangeInCapacity: add or remove the given percentage of the current capacity to itself. The number can be in the range [-100..100]. - ExactCapacity: set the capacity to this number. The number must be positive.
        :param lower: The lower bound of the interval. The scaling adjustment will be applied if the metric is higher than this value. Default: Threshold automatically derived from neighbouring intervals
        :param upper: The upper bound of the interval. The scaling adjustment will be applied if the metric is lower than this value. Default: Threshold automatically derived from neighbouring intervals

        Example::

            # The code below shows an example of how to instantiate this type.
            # The values are placeholders you should change.
            import aws_cdk.aws_applicationautoscaling as appscaling
            
            scaling_interval = appscaling.ScalingInterval(
                change=123,
            
                # the properties below are optional
                lower=123,
                upper=123
            )
        '''
        self._values: typing.Dict[str, typing.Any] = {
            "change": change,
        }
        if lower is not None:
            self._values["lower"] = lower
        if upper is not None:
            self._values["upper"] = upper

    @builtins.property
    def change(self) -> jsii.Number:
        '''The capacity adjustment to apply in this interval.

        The number is interpreted differently based on AdjustmentType:

        - ChangeInCapacity: add the adjustment to the current capacity.
          The number can be positive or negative.
        - PercentChangeInCapacity: add or remove the given percentage of the current
          capacity to itself. The number can be in the range [-100..100].
        - ExactCapacity: set the capacity to this number. The number must
          be positive.
        '''
        result = self._values.get("change")
        assert result is not None, "Required property 'change' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def lower(self) -> typing.Optional[jsii.Number]:
        '''The lower bound of the interval.

        The scaling adjustment will be applied if the metric is higher than this value.

        :default: Threshold automatically derived from neighbouring intervals
        '''
        result = self._values.get("lower")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def upper(self) -> typing.Optional[jsii.Number]:
        '''The upper bound of the interval.

        The scaling adjustment will be applied if the metric is lower than this value.

        :default: Threshold automatically derived from neighbouring intervals
        '''
        result = self._values.get("upper")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ScalingInterval(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk/aws-applicationautoscaling.ScalingSchedule",
    jsii_struct_bases=[],
    name_mapping={
        "end_time": "endTime",
        "max_capacity": "maxCapacity",
        "min_capacity": "minCapacity",
        "schedule": "schedule",
        "start_time": "startTime",
    },
)
class ScalingSchedule:
    def __init__(
        self,
        *,
        end_time: typing.Optional[datetime.datetime] = None,
        max_capacity: typing.Optional[jsii.Number] = None,
        min_capacity: typing.Optional[jsii.Number] = None,
        schedule: "Schedule",
        start_time: typing.Optional[datetime.datetime] = None,
    ) -> None:
        '''A scheduled scaling action.

        :param end_time: When this scheduled action expires. Default: The rule never expires.
        :param max_capacity: The new maximum capacity. During the scheduled time, the current capacity is above the maximum capacity, Application Auto Scaling scales in to the maximum capacity. At least one of maxCapacity and minCapacity must be supplied. Default: No new maximum capacity
        :param min_capacity: The new minimum capacity. During the scheduled time, if the current capacity is below the minimum capacity, Application Auto Scaling scales out to the minimum capacity. At least one of maxCapacity and minCapacity must be supplied. Default: No new minimum capacity
        :param schedule: When to perform this action.
        :param start_time: When this scheduled action becomes active. Default: The rule is activate immediately

        Example::

            # cluster is of type Cluster
            
            load_balanced_fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(self, "Service",
                cluster=cluster,
                memory_limit_mi_b=1024,
                desired_count=1,
                cpu=512,
                task_image_options=ecsPatterns.ApplicationLoadBalancedTaskImageOptions(
                    image=ecs.ContainerImage.from_registry("amazon/amazon-ecs-sample")
                )
            )
            
            scalable_target = load_balanced_fargate_service.service.auto_scale_task_count(
                min_capacity=5,
                max_capacity=20
            )
            
            scalable_target.scale_on_schedule("DaytimeScaleDown",
                schedule=appscaling.Schedule.cron(hour="8", minute="0"),
                min_capacity=1
            )
            
            scalable_target.scale_on_schedule("EveningRushScaleUp",
                schedule=appscaling.Schedule.cron(hour="20", minute="0"),
                min_capacity=10
            )
        '''
        self._values: typing.Dict[str, typing.Any] = {
            "schedule": schedule,
        }
        if end_time is not None:
            self._values["end_time"] = end_time
        if max_capacity is not None:
            self._values["max_capacity"] = max_capacity
        if min_capacity is not None:
            self._values["min_capacity"] = min_capacity
        if start_time is not None:
            self._values["start_time"] = start_time

    @builtins.property
    def end_time(self) -> typing.Optional[datetime.datetime]:
        '''When this scheduled action expires.

        :default: The rule never expires.
        '''
        result = self._values.get("end_time")
        return typing.cast(typing.Optional[datetime.datetime], result)

    @builtins.property
    def max_capacity(self) -> typing.Optional[jsii.Number]:
        '''The new maximum capacity.

        During the scheduled time, the current capacity is above the maximum
        capacity, Application Auto Scaling scales in to the maximum capacity.

        At least one of maxCapacity and minCapacity must be supplied.

        :default: No new maximum capacity
        '''
        result = self._values.get("max_capacity")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def min_capacity(self) -> typing.Optional[jsii.Number]:
        '''The new minimum capacity.

        During the scheduled time, if the current capacity is below the minimum
        capacity, Application Auto Scaling scales out to the minimum capacity.

        At least one of maxCapacity and minCapacity must be supplied.

        :default: No new minimum capacity
        '''
        result = self._values.get("min_capacity")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def schedule(self) -> "Schedule":
        '''When to perform this action.'''
        result = self._values.get("schedule")
        assert result is not None, "Required property 'schedule' is missing"
        return typing.cast("Schedule", result)

    @builtins.property
    def start_time(self) -> typing.Optional[datetime.datetime]:
        '''When this scheduled action becomes active.

        :default: The rule is activate immediately
        '''
        result = self._values.get("start_time")
        return typing.cast(typing.Optional[datetime.datetime], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ScalingSchedule(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class Schedule(
    metaclass=jsii.JSIIAbstractClass,
    jsii_type="@aws-cdk/aws-applicationautoscaling.Schedule",
):
    '''Schedule for scheduled scaling actions.

    Example::

        import aws_cdk.aws_autoscaling as autoscaling
        
        # fn is of type Function
        
        alias = lambda_.Alias(self, "Alias",
            alias_name="prod",
            version=fn.latest_version
        )
        
        # Create AutoScaling target
        as = alias.add_auto_scaling(max_capacity=50)
        
        # Configure Target Tracking
        as.scale_on_utilization(
            utilization_target=0.5
        )
        
        # Configure Scheduled Scaling
        as.scale_on_schedule("ScaleUpInTheMorning",
            schedule=autoscaling.Schedule.cron(hour="8", minute="0"),
            min_capacity=20
        )
    '''

    def __init__(self) -> None:
        jsii.create(self.__class__, self, [])

    @jsii.member(jsii_name="at") # type: ignore[misc]
    @builtins.classmethod
    def at(cls, moment: datetime.datetime) -> "Schedule":
        '''Construct a Schedule from a moment in time.

        :param moment: -
        '''
        return typing.cast("Schedule", jsii.sinvoke(cls, "at", [moment]))

    @jsii.member(jsii_name="cron") # type: ignore[misc]
    @builtins.classmethod
    def cron(
        cls,
        *,
        day: typing.Optional[builtins.str] = None,
        hour: typing.Optional[builtins.str] = None,
        minute: typing.Optional[builtins.str] = None,
        month: typing.Optional[builtins.str] = None,
        week_day: typing.Optional[builtins.str] = None,
        year: typing.Optional[builtins.str] = None,
    ) -> "Schedule":
        '''Create a schedule from a set of cron fields.

        :param day: The day of the month to run this rule at. Default: - Every day of the month
        :param hour: The hour to run this rule at. Default: - Every hour
        :param minute: The minute to run this rule at. Default: - Every minute
        :param month: The month to run this rule at. Default: - Every month
        :param week_day: The day of the week to run this rule at. Default: - Any day of the week
        :param year: The year to run this rule at. Default: - Every year
        '''
        options = CronOptions(
            day=day,
            hour=hour,
            minute=minute,
            month=month,
            week_day=week_day,
            year=year,
        )

        return typing.cast("Schedule", jsii.sinvoke(cls, "cron", [options]))

    @jsii.member(jsii_name="expression") # type: ignore[misc]
    @builtins.classmethod
    def expression(cls, expression: builtins.str) -> "Schedule":
        '''Construct a schedule from a literal schedule expression.

        :param expression: The expression to use. Must be in a format that Application AutoScaling will recognize
        '''
        return typing.cast("Schedule", jsii.sinvoke(cls, "expression", [expression]))

    @jsii.member(jsii_name="rate") # type: ignore[misc]
    @builtins.classmethod
    def rate(cls, duration: aws_cdk.core.Duration) -> "Schedule":
        '''Construct a schedule from an interval and a time unit.

        :param duration: -
        '''
        return typing.cast("Schedule", jsii.sinvoke(cls, "rate", [duration]))

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="expressionString")
    @abc.abstractmethod
    def expression_string(self) -> builtins.str:
        '''Retrieve the expression for this schedule.'''
        ...


class _ScheduleProxy(Schedule):
    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="expressionString")
    def expression_string(self) -> builtins.str:
        '''Retrieve the expression for this schedule.'''
        return typing.cast(builtins.str, jsii.get(self, "expressionString"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the abstract class
typing.cast(typing.Any, Schedule).__jsii_proxy_class__ = lambda : _ScheduleProxy


@jsii.enum(jsii_type="@aws-cdk/aws-applicationautoscaling.ServiceNamespace")
class ServiceNamespace(enum.Enum):
    '''The service that supports Application AutoScaling.

    Example::

        import aws_cdk.aws_lambda as lambda_
        
        # code is of type Code
        
        
        handler = lambda_.Function(self, "MyFunction",
            runtime=lambda_.Runtime.PYTHON_3_7,
            handler="index.handler",
            code=code,
        
            reserved_concurrent_executions=2
        )
        
        fn_ver = handler.add_version("CDKLambdaVersion", undefined, "demo alias", 10)
        
        target = appscaling.ScalableTarget(self, "ScalableTarget",
            service_namespace=appscaling.ServiceNamespace.LAMBDA,
            max_capacity=100,
            min_capacity=10,
            resource_id=f"function:{handler.functionName}:{fnVer.version}",
            scalable_dimension="lambda:function:ProvisionedConcurrency"
        )
        
        target.scale_to_track_metric("PceTracking",
            target_value=0.9,
            predefined_metric=appscaling.PredefinedMetric.LAMBDA_PROVISIONED_CONCURRENCY_UTILIZATION
        )
    '''

    APPSTREAM = "APPSTREAM"
    '''App Stream.'''
    COMPREHEND = "COMPREHEND"
    '''Comprehend.'''
    CUSTOM_RESOURCE = "CUSTOM_RESOURCE"
    '''Custom Resource.'''
    DYNAMODB = "DYNAMODB"
    '''Dynamo DB.'''
    EC2 = "EC2"
    '''Elastic Compute Cloud.'''
    ECS = "ECS"
    '''Elastic Container Service.'''
    ELASTIC_MAP_REDUCE = "ELASTIC_MAP_REDUCE"
    '''Elastic Map Reduce.'''
    KAFKA = "KAFKA"
    '''Kafka.'''
    LAMBDA = "LAMBDA"
    '''Lambda.'''
    RDS = "RDS"
    '''Relational Database Service.'''
    SAGEMAKER = "SAGEMAKER"
    '''SageMaker.'''


class StepScalingAction(
    aws_cdk.core.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk/aws-applicationautoscaling.StepScalingAction",
):
    '''Define a step scaling action.

    This kind of scaling policy adjusts the target capacity in configurable
    steps. The size of the step is configurable based on the metric's distance
    to its alarm threshold.

    This Action must be used as the target of a CloudWatch alarm to take effect.

    Example::

        # The code below shows an example of how to instantiate this type.
        # The values are placeholders you should change.
        import aws_cdk.aws_applicationautoscaling as appscaling
        import aws_cdk.core as cdk
        
        # scalable_target is of type ScalableTarget
        
        step_scaling_action = appscaling.StepScalingAction(self, "MyStepScalingAction",
            scaling_target=scalable_target,
        
            # the properties below are optional
            adjustment_type=appscaling.AdjustmentType.CHANGE_IN_CAPACITY,
            cooldown=cdk.Duration.minutes(30),
            metric_aggregation_type=appscaling.MetricAggregationType.AVERAGE,
            min_adjustment_magnitude=123,
            policy_name="policyName"
        )
    '''

    def __init__(
        self,
        scope: constructs.Construct,
        id: builtins.str,
        *,
        adjustment_type: typing.Optional[AdjustmentType] = None,
        cooldown: typing.Optional[aws_cdk.core.Duration] = None,
        metric_aggregation_type: typing.Optional[MetricAggregationType] = None,
        min_adjustment_magnitude: typing.Optional[jsii.Number] = None,
        policy_name: typing.Optional[builtins.str] = None,
        scaling_target: IScalableTarget,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param adjustment_type: How the adjustment numbers are interpreted. Default: ChangeInCapacity
        :param cooldown: Grace period after scaling activity. For scale out policies, multiple scale outs during the cooldown period are squashed so that only the biggest scale out happens. For scale in policies, subsequent scale ins during the cooldown period are ignored. Default: No cooldown period
        :param metric_aggregation_type: The aggregation type for the CloudWatch metrics. Default: Average
        :param min_adjustment_magnitude: Minimum absolute number to adjust capacity with as result of percentage scaling. Only when using AdjustmentType = PercentChangeInCapacity, this number controls the minimum absolute effect size. Default: No minimum scaling effect
        :param policy_name: A name for the scaling policy. Default: Automatically generated name
        :param scaling_target: The scalable target.
        '''
        props = StepScalingActionProps(
            adjustment_type=adjustment_type,
            cooldown=cooldown,
            metric_aggregation_type=metric_aggregation_type,
            min_adjustment_magnitude=min_adjustment_magnitude,
            policy_name=policy_name,
            scaling_target=scaling_target,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="addAdjustment")
    def add_adjustment(
        self,
        *,
        adjustment: jsii.Number,
        lower_bound: typing.Optional[jsii.Number] = None,
        upper_bound: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''Add an adjusment interval to the ScalingAction.

        :param adjustment: What number to adjust the capacity with. The number is interpeted as an added capacity, a new fixed capacity or an added percentage depending on the AdjustmentType value of the StepScalingPolicy. Can be positive or negative.
        :param lower_bound: Lower bound where this scaling tier applies. The scaling tier applies if the difference between the metric value and its alarm threshold is higher than this value. Default: -Infinity if this is the first tier, otherwise the upperBound of the previous tier
        :param upper_bound: Upper bound where this scaling tier applies. The scaling tier applies if the difference between the metric value and its alarm threshold is lower than this value. Default: +Infinity
        '''
        adjustment_ = AdjustmentTier(
            adjustment=adjustment, lower_bound=lower_bound, upper_bound=upper_bound
        )

        return typing.cast(None, jsii.invoke(self, "addAdjustment", [adjustment_]))

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="scalingPolicyArn")
    def scaling_policy_arn(self) -> builtins.str:
        '''ARN of the scaling policy.'''
        return typing.cast(builtins.str, jsii.get(self, "scalingPolicyArn"))


@jsii.data_type(
    jsii_type="@aws-cdk/aws-applicationautoscaling.StepScalingActionProps",
    jsii_struct_bases=[],
    name_mapping={
        "adjustment_type": "adjustmentType",
        "cooldown": "cooldown",
        "metric_aggregation_type": "metricAggregationType",
        "min_adjustment_magnitude": "minAdjustmentMagnitude",
        "policy_name": "policyName",
        "scaling_target": "scalingTarget",
    },
)
class StepScalingActionProps:
    def __init__(
        self,
        *,
        adjustment_type: typing.Optional[AdjustmentType] = None,
        cooldown: typing.Optional[aws_cdk.core.Duration] = None,
        metric_aggregation_type: typing.Optional[MetricAggregationType] = None,
        min_adjustment_magnitude: typing.Optional[jsii.Number] = None,
        policy_name: typing.Optional[builtins.str] = None,
        scaling_target: IScalableTarget,
    ) -> None:
        '''Properties for a scaling policy.

        :param adjustment_type: How the adjustment numbers are interpreted. Default: ChangeInCapacity
        :param cooldown: Grace period after scaling activity. For scale out policies, multiple scale outs during the cooldown period are squashed so that only the biggest scale out happens. For scale in policies, subsequent scale ins during the cooldown period are ignored. Default: No cooldown period
        :param metric_aggregation_type: The aggregation type for the CloudWatch metrics. Default: Average
        :param min_adjustment_magnitude: Minimum absolute number to adjust capacity with as result of percentage scaling. Only when using AdjustmentType = PercentChangeInCapacity, this number controls the minimum absolute effect size. Default: No minimum scaling effect
        :param policy_name: A name for the scaling policy. Default: Automatically generated name
        :param scaling_target: The scalable target.

        Example::

            # The code below shows an example of how to instantiate this type.
            # The values are placeholders you should change.
            import aws_cdk.aws_applicationautoscaling as appscaling
            import aws_cdk.core as cdk
            
            # scalable_target is of type ScalableTarget
            
            step_scaling_action_props = appscaling.StepScalingActionProps(
                scaling_target=scalable_target,
            
                # the properties below are optional
                adjustment_type=appscaling.AdjustmentType.CHANGE_IN_CAPACITY,
                cooldown=cdk.Duration.minutes(30),
                metric_aggregation_type=appscaling.MetricAggregationType.AVERAGE,
                min_adjustment_magnitude=123,
                policy_name="policyName"
            )
        '''
        self._values: typing.Dict[str, typing.Any] = {
            "scaling_target": scaling_target,
        }
        if adjustment_type is not None:
            self._values["adjustment_type"] = adjustment_type
        if cooldown is not None:
            self._values["cooldown"] = cooldown
        if metric_aggregation_type is not None:
            self._values["metric_aggregation_type"] = metric_aggregation_type
        if min_adjustment_magnitude is not None:
            self._values["min_adjustment_magnitude"] = min_adjustment_magnitude
        if policy_name is not None:
            self._values["policy_name"] = policy_name

    @builtins.property
    def adjustment_type(self) -> typing.Optional[AdjustmentType]:
        '''How the adjustment numbers are interpreted.

        :default: ChangeInCapacity
        '''
        result = self._values.get("adjustment_type")
        return typing.cast(typing.Optional[AdjustmentType], result)

    @builtins.property
    def cooldown(self) -> typing.Optional[aws_cdk.core.Duration]:
        '''Grace period after scaling activity.

        For scale out policies, multiple scale outs during the cooldown period are
        squashed so that only the biggest scale out happens.

        For scale in policies, subsequent scale ins during the cooldown period are
        ignored.

        :default: No cooldown period

        :see: https://docs.aws.amazon.com/autoscaling/application/APIReference/API_StepScalingPolicyConfiguration.html
        '''
        result = self._values.get("cooldown")
        return typing.cast(typing.Optional[aws_cdk.core.Duration], result)

    @builtins.property
    def metric_aggregation_type(self) -> typing.Optional[MetricAggregationType]:
        '''The aggregation type for the CloudWatch metrics.

        :default: Average
        '''
        result = self._values.get("metric_aggregation_type")
        return typing.cast(typing.Optional[MetricAggregationType], result)

    @builtins.property
    def min_adjustment_magnitude(self) -> typing.Optional[jsii.Number]:
        '''Minimum absolute number to adjust capacity with as result of percentage scaling.

        Only when using AdjustmentType = PercentChangeInCapacity, this number controls
        the minimum absolute effect size.

        :default: No minimum scaling effect
        '''
        result = self._values.get("min_adjustment_magnitude")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def policy_name(self) -> typing.Optional[builtins.str]:
        '''A name for the scaling policy.

        :default: Automatically generated name
        '''
        result = self._values.get("policy_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def scaling_target(self) -> IScalableTarget:
        '''The scalable target.'''
        result = self._values.get("scaling_target")
        assert result is not None, "Required property 'scaling_target' is missing"
        return typing.cast(IScalableTarget, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "StepScalingActionProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class StepScalingPolicy(
    aws_cdk.core.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk/aws-applicationautoscaling.StepScalingPolicy",
):
    '''Define a scaling strategy which scales depending on absolute values of some metric.

    You can specify the scaling behavior for various values of the metric.

    Implemented using one or more CloudWatch alarms and Step Scaling Policies.

    Example::

        # The code below shows an example of how to instantiate this type.
        # The values are placeholders you should change.
        import aws_cdk.aws_applicationautoscaling as appscaling
        import aws_cdk.aws_cloudwatch as cloudwatch
        import aws_cdk.core as cdk
        
        # metric is of type Metric
        # scalable_target is of type ScalableTarget
        
        step_scaling_policy = appscaling.StepScalingPolicy(self, "MyStepScalingPolicy",
            metric=metric,
            scaling_steps=[appscaling.ScalingInterval(
                change=123,
        
                # the properties below are optional
                lower=123,
                upper=123
            )],
            scaling_target=scalable_target,
        
            # the properties below are optional
            adjustment_type=appscaling.AdjustmentType.CHANGE_IN_CAPACITY,
            cooldown=cdk.Duration.minutes(30),
            evaluation_periods=123,
            metric_aggregation_type=appscaling.MetricAggregationType.AVERAGE,
            min_adjustment_magnitude=123
        )
    '''

    def __init__(
        self,
        scope: constructs.Construct,
        id: builtins.str,
        *,
        scaling_target: IScalableTarget,
        adjustment_type: typing.Optional[AdjustmentType] = None,
        cooldown: typing.Optional[aws_cdk.core.Duration] = None,
        evaluation_periods: typing.Optional[jsii.Number] = None,
        metric: aws_cdk.aws_cloudwatch.IMetric,
        metric_aggregation_type: typing.Optional[MetricAggregationType] = None,
        min_adjustment_magnitude: typing.Optional[jsii.Number] = None,
        scaling_steps: typing.Sequence[ScalingInterval],
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param scaling_target: The scaling target.
        :param adjustment_type: How the adjustment numbers inside 'intervals' are interpreted. Default: ChangeInCapacity
        :param cooldown: Grace period after scaling activity. Subsequent scale outs during the cooldown period are squashed so that only the biggest scale out happens. Subsequent scale ins during the cooldown period are ignored. Default: No cooldown period
        :param evaluation_periods: How many evaluation periods of the metric to wait before triggering a scaling action. Raising this value can be used to smooth out the metric, at the expense of slower response times. Default: 1
        :param metric: Metric to scale on.
        :param metric_aggregation_type: Aggregation to apply to all data points over the evaluation periods. Only has meaning if ``evaluationPeriods != 1``. Default: - The statistic from the metric if applicable (MIN, MAX, AVERAGE), otherwise AVERAGE.
        :param min_adjustment_magnitude: Minimum absolute number to adjust capacity with as result of percentage scaling. Only when using AdjustmentType = PercentChangeInCapacity, this number controls the minimum absolute effect size. Default: No minimum scaling effect
        :param scaling_steps: The intervals for scaling. Maps a range of metric values to a particular scaling behavior.
        '''
        props = StepScalingPolicyProps(
            scaling_target=scaling_target,
            adjustment_type=adjustment_type,
            cooldown=cooldown,
            evaluation_periods=evaluation_periods,
            metric=metric,
            metric_aggregation_type=metric_aggregation_type,
            min_adjustment_magnitude=min_adjustment_magnitude,
            scaling_steps=scaling_steps,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="lowerAction")
    def lower_action(self) -> typing.Optional[StepScalingAction]:
        return typing.cast(typing.Optional[StepScalingAction], jsii.get(self, "lowerAction"))

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="lowerAlarm")
    def lower_alarm(self) -> typing.Optional[aws_cdk.aws_cloudwatch.Alarm]:
        return typing.cast(typing.Optional[aws_cdk.aws_cloudwatch.Alarm], jsii.get(self, "lowerAlarm"))

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="upperAction")
    def upper_action(self) -> typing.Optional[StepScalingAction]:
        return typing.cast(typing.Optional[StepScalingAction], jsii.get(self, "upperAction"))

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="upperAlarm")
    def upper_alarm(self) -> typing.Optional[aws_cdk.aws_cloudwatch.Alarm]:
        return typing.cast(typing.Optional[aws_cdk.aws_cloudwatch.Alarm], jsii.get(self, "upperAlarm"))


@jsii.data_type(
    jsii_type="@aws-cdk/aws-applicationautoscaling.StepScalingPolicyProps",
    jsii_struct_bases=[BasicStepScalingPolicyProps],
    name_mapping={
        "adjustment_type": "adjustmentType",
        "cooldown": "cooldown",
        "evaluation_periods": "evaluationPeriods",
        "metric": "metric",
        "metric_aggregation_type": "metricAggregationType",
        "min_adjustment_magnitude": "minAdjustmentMagnitude",
        "scaling_steps": "scalingSteps",
        "scaling_target": "scalingTarget",
    },
)
class StepScalingPolicyProps(BasicStepScalingPolicyProps):
    def __init__(
        self,
        *,
        adjustment_type: typing.Optional[AdjustmentType] = None,
        cooldown: typing.Optional[aws_cdk.core.Duration] = None,
        evaluation_periods: typing.Optional[jsii.Number] = None,
        metric: aws_cdk.aws_cloudwatch.IMetric,
        metric_aggregation_type: typing.Optional[MetricAggregationType] = None,
        min_adjustment_magnitude: typing.Optional[jsii.Number] = None,
        scaling_steps: typing.Sequence[ScalingInterval],
        scaling_target: IScalableTarget,
    ) -> None:
        '''
        :param adjustment_type: How the adjustment numbers inside 'intervals' are interpreted. Default: ChangeInCapacity
        :param cooldown: Grace period after scaling activity. Subsequent scale outs during the cooldown period are squashed so that only the biggest scale out happens. Subsequent scale ins during the cooldown period are ignored. Default: No cooldown period
        :param evaluation_periods: How many evaluation periods of the metric to wait before triggering a scaling action. Raising this value can be used to smooth out the metric, at the expense of slower response times. Default: 1
        :param metric: Metric to scale on.
        :param metric_aggregation_type: Aggregation to apply to all data points over the evaluation periods. Only has meaning if ``evaluationPeriods != 1``. Default: - The statistic from the metric if applicable (MIN, MAX, AVERAGE), otherwise AVERAGE.
        :param min_adjustment_magnitude: Minimum absolute number to adjust capacity with as result of percentage scaling. Only when using AdjustmentType = PercentChangeInCapacity, this number controls the minimum absolute effect size. Default: No minimum scaling effect
        :param scaling_steps: The intervals for scaling. Maps a range of metric values to a particular scaling behavior.
        :param scaling_target: The scaling target.

        Example::

            # The code below shows an example of how to instantiate this type.
            # The values are placeholders you should change.
            import aws_cdk.aws_applicationautoscaling as appscaling
            import aws_cdk.aws_cloudwatch as cloudwatch
            import aws_cdk.core as cdk
            
            # metric is of type Metric
            # scalable_target is of type ScalableTarget
            
            step_scaling_policy_props = appscaling.StepScalingPolicyProps(
                metric=metric,
                scaling_steps=[appscaling.ScalingInterval(
                    change=123,
            
                    # the properties below are optional
                    lower=123,
                    upper=123
                )],
                scaling_target=scalable_target,
            
                # the properties below are optional
                adjustment_type=appscaling.AdjustmentType.CHANGE_IN_CAPACITY,
                cooldown=cdk.Duration.minutes(30),
                evaluation_periods=123,
                metric_aggregation_type=appscaling.MetricAggregationType.AVERAGE,
                min_adjustment_magnitude=123
            )
        '''
        self._values: typing.Dict[str, typing.Any] = {
            "metric": metric,
            "scaling_steps": scaling_steps,
            "scaling_target": scaling_target,
        }
        if adjustment_type is not None:
            self._values["adjustment_type"] = adjustment_type
        if cooldown is not None:
            self._values["cooldown"] = cooldown
        if evaluation_periods is not None:
            self._values["evaluation_periods"] = evaluation_periods
        if metric_aggregation_type is not None:
            self._values["metric_aggregation_type"] = metric_aggregation_type
        if min_adjustment_magnitude is not None:
            self._values["min_adjustment_magnitude"] = min_adjustment_magnitude

    @builtins.property
    def adjustment_type(self) -> typing.Optional[AdjustmentType]:
        '''How the adjustment numbers inside 'intervals' are interpreted.

        :default: ChangeInCapacity
        '''
        result = self._values.get("adjustment_type")
        return typing.cast(typing.Optional[AdjustmentType], result)

    @builtins.property
    def cooldown(self) -> typing.Optional[aws_cdk.core.Duration]:
        '''Grace period after scaling activity.

        Subsequent scale outs during the cooldown period are squashed so that only
        the biggest scale out happens.

        Subsequent scale ins during the cooldown period are ignored.

        :default: No cooldown period

        :see: https://docs.aws.amazon.com/autoscaling/application/APIReference/API_StepScalingPolicyConfiguration.html
        '''
        result = self._values.get("cooldown")
        return typing.cast(typing.Optional[aws_cdk.core.Duration], result)

    @builtins.property
    def evaluation_periods(self) -> typing.Optional[jsii.Number]:
        '''How many evaluation periods of the metric to wait before triggering a scaling action.

        Raising this value can be used to smooth out the metric, at the expense
        of slower response times.

        :default: 1
        '''
        result = self._values.get("evaluation_periods")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def metric(self) -> aws_cdk.aws_cloudwatch.IMetric:
        '''Metric to scale on.'''
        result = self._values.get("metric")
        assert result is not None, "Required property 'metric' is missing"
        return typing.cast(aws_cdk.aws_cloudwatch.IMetric, result)

    @builtins.property
    def metric_aggregation_type(self) -> typing.Optional[MetricAggregationType]:
        '''Aggregation to apply to all data points over the evaluation periods.

        Only has meaning if ``evaluationPeriods != 1``.

        :default: - The statistic from the metric if applicable (MIN, MAX, AVERAGE), otherwise AVERAGE.
        '''
        result = self._values.get("metric_aggregation_type")
        return typing.cast(typing.Optional[MetricAggregationType], result)

    @builtins.property
    def min_adjustment_magnitude(self) -> typing.Optional[jsii.Number]:
        '''Minimum absolute number to adjust capacity with as result of percentage scaling.

        Only when using AdjustmentType = PercentChangeInCapacity, this number controls
        the minimum absolute effect size.

        :default: No minimum scaling effect
        '''
        result = self._values.get("min_adjustment_magnitude")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def scaling_steps(self) -> typing.List[ScalingInterval]:
        '''The intervals for scaling.

        Maps a range of metric values to a particular scaling behavior.
        '''
        result = self._values.get("scaling_steps")
        assert result is not None, "Required property 'scaling_steps' is missing"
        return typing.cast(typing.List[ScalingInterval], result)

    @builtins.property
    def scaling_target(self) -> IScalableTarget:
        '''The scaling target.'''
        result = self._values.get("scaling_target")
        assert result is not None, "Required property 'scaling_target' is missing"
        return typing.cast(IScalableTarget, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "StepScalingPolicyProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class TargetTrackingScalingPolicy(
    aws_cdk.core.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-cdk/aws-applicationautoscaling.TargetTrackingScalingPolicy",
):
    '''
    Example::

        # The code below shows an example of how to instantiate this type.
        # The values are placeholders you should change.
        import aws_cdk.aws_applicationautoscaling as appscaling
        import aws_cdk.aws_cloudwatch as cloudwatch
        import aws_cdk.core as cdk
        
        # metric is of type Metric
        # scalable_target is of type ScalableTarget
        
        target_tracking_scaling_policy = appscaling.TargetTrackingScalingPolicy(self, "MyTargetTrackingScalingPolicy",
            scaling_target=scalable_target,
            target_value=123,
        
            # the properties below are optional
            custom_metric=metric,
            disable_scale_in=False,
            policy_name="policyName",
            predefined_metric=appscaling.PredefinedMetric.DYNAMODB_READ_CAPACITY_UTILIZATION,
            resource_label="resourceLabel",
            scale_in_cooldown=cdk.Duration.minutes(30),
            scale_out_cooldown=cdk.Duration.minutes(30)
        )
    '''

    def __init__(
        self,
        scope: constructs.Construct,
        id: builtins.str,
        *,
        scaling_target: IScalableTarget,
        custom_metric: typing.Optional[aws_cdk.aws_cloudwatch.IMetric] = None,
        predefined_metric: typing.Optional[PredefinedMetric] = None,
        resource_label: typing.Optional[builtins.str] = None,
        target_value: jsii.Number,
        disable_scale_in: typing.Optional[builtins.bool] = None,
        policy_name: typing.Optional[builtins.str] = None,
        scale_in_cooldown: typing.Optional[aws_cdk.core.Duration] = None,
        scale_out_cooldown: typing.Optional[aws_cdk.core.Duration] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param scaling_target: 
        :param custom_metric: A custom metric for application autoscaling. The metric must track utilization. Scaling out will happen if the metric is higher than the target value, scaling in will happen in the metric is lower than the target value. Exactly one of customMetric or predefinedMetric must be specified. Default: - No custom metric.
        :param predefined_metric: A predefined metric for application autoscaling. The metric must track utilization. Scaling out will happen if the metric is higher than the target value, scaling in will happen in the metric is lower than the target value. Exactly one of customMetric or predefinedMetric must be specified. Default: - No predefined metrics.
        :param resource_label: Identify the resource associated with the metric type. Only used for predefined metric ALBRequestCountPerTarget. Example value: ``app/<load-balancer-name>/<load-balancer-id>/targetgroup/<target-group-name>/<target-group-id>`` Default: - No resource label.
        :param target_value: The target value for the metric.
        :param disable_scale_in: Indicates whether scale in by the target tracking policy is disabled. If the value is true, scale in is disabled and the target tracking policy won't remove capacity from the scalable resource. Otherwise, scale in is enabled and the target tracking policy can remove capacity from the scalable resource. Default: false
        :param policy_name: A name for the scaling policy. Default: - Automatically generated name.
        :param scale_in_cooldown: Period after a scale in activity completes before another scale in activity can start. Default: Duration.seconds(300) for the following scalable targets: ECS services, Spot Fleet requests, EMR clusters, AppStream 2.0 fleets, Aurora DB clusters, Amazon SageMaker endpoint variants, Custom resources. For all other scalable targets, the default value is Duration.seconds(0): DynamoDB tables, DynamoDB global secondary indexes, Amazon Comprehend document classification endpoints, Lambda provisioned concurrency
        :param scale_out_cooldown: Period after a scale out activity completes before another scale out activity can start. Default: Duration.seconds(300) for the following scalable targets: ECS services, Spot Fleet requests, EMR clusters, AppStream 2.0 fleets, Aurora DB clusters, Amazon SageMaker endpoint variants, Custom resources. For all other scalable targets, the default value is Duration.seconds(0): DynamoDB tables, DynamoDB global secondary indexes, Amazon Comprehend document classification endpoints, Lambda provisioned concurrency
        '''
        props = TargetTrackingScalingPolicyProps(
            scaling_target=scaling_target,
            custom_metric=custom_metric,
            predefined_metric=predefined_metric,
            resource_label=resource_label,
            target_value=target_value,
            disable_scale_in=disable_scale_in,
            policy_name=policy_name,
            scale_in_cooldown=scale_in_cooldown,
            scale_out_cooldown=scale_out_cooldown,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="scalingPolicyArn")
    def scaling_policy_arn(self) -> builtins.str:
        '''ARN of the scaling policy.'''
        return typing.cast(builtins.str, jsii.get(self, "scalingPolicyArn"))


@jsii.data_type(
    jsii_type="@aws-cdk/aws-applicationautoscaling.TargetTrackingScalingPolicyProps",
    jsii_struct_bases=[BasicTargetTrackingScalingPolicyProps],
    name_mapping={
        "disable_scale_in": "disableScaleIn",
        "policy_name": "policyName",
        "scale_in_cooldown": "scaleInCooldown",
        "scale_out_cooldown": "scaleOutCooldown",
        "custom_metric": "customMetric",
        "predefined_metric": "predefinedMetric",
        "resource_label": "resourceLabel",
        "target_value": "targetValue",
        "scaling_target": "scalingTarget",
    },
)
class TargetTrackingScalingPolicyProps(BasicTargetTrackingScalingPolicyProps):
    def __init__(
        self,
        *,
        disable_scale_in: typing.Optional[builtins.bool] = None,
        policy_name: typing.Optional[builtins.str] = None,
        scale_in_cooldown: typing.Optional[aws_cdk.core.Duration] = None,
        scale_out_cooldown: typing.Optional[aws_cdk.core.Duration] = None,
        custom_metric: typing.Optional[aws_cdk.aws_cloudwatch.IMetric] = None,
        predefined_metric: typing.Optional[PredefinedMetric] = None,
        resource_label: typing.Optional[builtins.str] = None,
        target_value: jsii.Number,
        scaling_target: IScalableTarget,
    ) -> None:
        '''Properties for a concrete TargetTrackingPolicy.

        Adds the scalingTarget.

        :param disable_scale_in: Indicates whether scale in by the target tracking policy is disabled. If the value is true, scale in is disabled and the target tracking policy won't remove capacity from the scalable resource. Otherwise, scale in is enabled and the target tracking policy can remove capacity from the scalable resource. Default: false
        :param policy_name: A name for the scaling policy. Default: - Automatically generated name.
        :param scale_in_cooldown: Period after a scale in activity completes before another scale in activity can start. Default: Duration.seconds(300) for the following scalable targets: ECS services, Spot Fleet requests, EMR clusters, AppStream 2.0 fleets, Aurora DB clusters, Amazon SageMaker endpoint variants, Custom resources. For all other scalable targets, the default value is Duration.seconds(0): DynamoDB tables, DynamoDB global secondary indexes, Amazon Comprehend document classification endpoints, Lambda provisioned concurrency
        :param scale_out_cooldown: Period after a scale out activity completes before another scale out activity can start. Default: Duration.seconds(300) for the following scalable targets: ECS services, Spot Fleet requests, EMR clusters, AppStream 2.0 fleets, Aurora DB clusters, Amazon SageMaker endpoint variants, Custom resources. For all other scalable targets, the default value is Duration.seconds(0): DynamoDB tables, DynamoDB global secondary indexes, Amazon Comprehend document classification endpoints, Lambda provisioned concurrency
        :param custom_metric: A custom metric for application autoscaling. The metric must track utilization. Scaling out will happen if the metric is higher than the target value, scaling in will happen in the metric is lower than the target value. Exactly one of customMetric or predefinedMetric must be specified. Default: - No custom metric.
        :param predefined_metric: A predefined metric for application autoscaling. The metric must track utilization. Scaling out will happen if the metric is higher than the target value, scaling in will happen in the metric is lower than the target value. Exactly one of customMetric or predefinedMetric must be specified. Default: - No predefined metrics.
        :param resource_label: Identify the resource associated with the metric type. Only used for predefined metric ALBRequestCountPerTarget. Example value: ``app/<load-balancer-name>/<load-balancer-id>/targetgroup/<target-group-name>/<target-group-id>`` Default: - No resource label.
        :param target_value: The target value for the metric.
        :param scaling_target: 

        Example::

            # The code below shows an example of how to instantiate this type.
            # The values are placeholders you should change.
            import aws_cdk.aws_applicationautoscaling as appscaling
            import aws_cdk.aws_cloudwatch as cloudwatch
            import aws_cdk.core as cdk
            
            # metric is of type Metric
            # scalable_target is of type ScalableTarget
            
            target_tracking_scaling_policy_props = appscaling.TargetTrackingScalingPolicyProps(
                scaling_target=scalable_target,
                target_value=123,
            
                # the properties below are optional
                custom_metric=metric,
                disable_scale_in=False,
                policy_name="policyName",
                predefined_metric=appscaling.PredefinedMetric.DYNAMODB_READ_CAPACITY_UTILIZATION,
                resource_label="resourceLabel",
                scale_in_cooldown=cdk.Duration.minutes(30),
                scale_out_cooldown=cdk.Duration.minutes(30)
            )
        '''
        self._values: typing.Dict[str, typing.Any] = {
            "target_value": target_value,
            "scaling_target": scaling_target,
        }
        if disable_scale_in is not None:
            self._values["disable_scale_in"] = disable_scale_in
        if policy_name is not None:
            self._values["policy_name"] = policy_name
        if scale_in_cooldown is not None:
            self._values["scale_in_cooldown"] = scale_in_cooldown
        if scale_out_cooldown is not None:
            self._values["scale_out_cooldown"] = scale_out_cooldown
        if custom_metric is not None:
            self._values["custom_metric"] = custom_metric
        if predefined_metric is not None:
            self._values["predefined_metric"] = predefined_metric
        if resource_label is not None:
            self._values["resource_label"] = resource_label

    @builtins.property
    def disable_scale_in(self) -> typing.Optional[builtins.bool]:
        '''Indicates whether scale in by the target tracking policy is disabled.

        If the value is true, scale in is disabled and the target tracking policy
        won't remove capacity from the scalable resource. Otherwise, scale in is
        enabled and the target tracking policy can remove capacity from the
        scalable resource.

        :default: false
        '''
        result = self._values.get("disable_scale_in")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def policy_name(self) -> typing.Optional[builtins.str]:
        '''A name for the scaling policy.

        :default: - Automatically generated name.
        '''
        result = self._values.get("policy_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def scale_in_cooldown(self) -> typing.Optional[aws_cdk.core.Duration]:
        '''Period after a scale in activity completes before another scale in activity can start.

        :default:

        Duration.seconds(300) for the following scalable targets: ECS services,
        Spot Fleet requests, EMR clusters, AppStream 2.0 fleets, Aurora DB clusters,
        Amazon SageMaker endpoint variants, Custom resources. For all other scalable
        targets, the default value is Duration.seconds(0): DynamoDB tables, DynamoDB
        global secondary indexes, Amazon Comprehend document classification endpoints,
        Lambda provisioned concurrency
        '''
        result = self._values.get("scale_in_cooldown")
        return typing.cast(typing.Optional[aws_cdk.core.Duration], result)

    @builtins.property
    def scale_out_cooldown(self) -> typing.Optional[aws_cdk.core.Duration]:
        '''Period after a scale out activity completes before another scale out activity can start.

        :default:

        Duration.seconds(300) for the following scalable targets: ECS services,
        Spot Fleet requests, EMR clusters, AppStream 2.0 fleets, Aurora DB clusters,
        Amazon SageMaker endpoint variants, Custom resources. For all other scalable
        targets, the default value is Duration.seconds(0): DynamoDB tables, DynamoDB
        global secondary indexes, Amazon Comprehend document classification endpoints,
        Lambda provisioned concurrency
        '''
        result = self._values.get("scale_out_cooldown")
        return typing.cast(typing.Optional[aws_cdk.core.Duration], result)

    @builtins.property
    def custom_metric(self) -> typing.Optional[aws_cdk.aws_cloudwatch.IMetric]:
        '''A custom metric for application autoscaling.

        The metric must track utilization. Scaling out will happen if the metric is higher than
        the target value, scaling in will happen in the metric is lower than the target value.

        Exactly one of customMetric or predefinedMetric must be specified.

        :default: - No custom metric.
        '''
        result = self._values.get("custom_metric")
        return typing.cast(typing.Optional[aws_cdk.aws_cloudwatch.IMetric], result)

    @builtins.property
    def predefined_metric(self) -> typing.Optional[PredefinedMetric]:
        '''A predefined metric for application autoscaling.

        The metric must track utilization. Scaling out will happen if the metric is higher than
        the target value, scaling in will happen in the metric is lower than the target value.

        Exactly one of customMetric or predefinedMetric must be specified.

        :default: - No predefined metrics.
        '''
        result = self._values.get("predefined_metric")
        return typing.cast(typing.Optional[PredefinedMetric], result)

    @builtins.property
    def resource_label(self) -> typing.Optional[builtins.str]:
        '''Identify the resource associated with the metric type.

        Only used for predefined metric ALBRequestCountPerTarget.

        Example value: ``app/<load-balancer-name>/<load-balancer-id>/targetgroup/<target-group-name>/<target-group-id>``

        :default: - No resource label.
        '''
        result = self._values.get("resource_label")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def target_value(self) -> jsii.Number:
        '''The target value for the metric.'''
        result = self._values.get("target_value")
        assert result is not None, "Required property 'target_value' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def scaling_target(self) -> IScalableTarget:
        result = self._values.get("scaling_target")
        assert result is not None, "Required property 'scaling_target' is missing"
        return typing.cast(IScalableTarget, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "TargetTrackingScalingPolicyProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@aws-cdk/aws-applicationautoscaling.BaseScalableAttributeProps",
    jsii_struct_bases=[EnableScalingProps],
    name_mapping={
        "max_capacity": "maxCapacity",
        "min_capacity": "minCapacity",
        "dimension": "dimension",
        "resource_id": "resourceId",
        "role": "role",
        "service_namespace": "serviceNamespace",
    },
)
class BaseScalableAttributeProps(EnableScalingProps):
    def __init__(
        self,
        *,
        max_capacity: jsii.Number,
        min_capacity: typing.Optional[jsii.Number] = None,
        dimension: builtins.str,
        resource_id: builtins.str,
        role: aws_cdk.aws_iam.IRole,
        service_namespace: ServiceNamespace,
    ) -> None:
        '''Properties for a ScalableTableAttribute.

        :param max_capacity: Maximum capacity to scale to.
        :param min_capacity: Minimum capacity to scale to. Default: 1
        :param dimension: Scalable dimension of the attribute.
        :param resource_id: Resource ID of the attribute.
        :param role: Role to use for scaling.
        :param service_namespace: Service namespace of the scalable attribute.

        Example::

            # The code below shows an example of how to instantiate this type.
            # The values are placeholders you should change.
            import aws_cdk.aws_applicationautoscaling as appscaling
            import aws_cdk.aws_iam as iam
            
            # role is of type Role
            
            base_scalable_attribute_props = appscaling.BaseScalableAttributeProps(
                dimension="dimension",
                max_capacity=123,
                resource_id="resourceId",
                role=role,
                service_namespace=appscaling.ServiceNamespace.ECS,
            
                # the properties below are optional
                min_capacity=123
            )
        '''
        self._values: typing.Dict[str, typing.Any] = {
            "max_capacity": max_capacity,
            "dimension": dimension,
            "resource_id": resource_id,
            "role": role,
            "service_namespace": service_namespace,
        }
        if min_capacity is not None:
            self._values["min_capacity"] = min_capacity

    @builtins.property
    def max_capacity(self) -> jsii.Number:
        '''Maximum capacity to scale to.'''
        result = self._values.get("max_capacity")
        assert result is not None, "Required property 'max_capacity' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def min_capacity(self) -> typing.Optional[jsii.Number]:
        '''Minimum capacity to scale to.

        :default: 1
        '''
        result = self._values.get("min_capacity")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def dimension(self) -> builtins.str:
        '''Scalable dimension of the attribute.'''
        result = self._values.get("dimension")
        assert result is not None, "Required property 'dimension' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def resource_id(self) -> builtins.str:
        '''Resource ID of the attribute.'''
        result = self._values.get("resource_id")
        assert result is not None, "Required property 'resource_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def role(self) -> aws_cdk.aws_iam.IRole:
        '''Role to use for scaling.'''
        result = self._values.get("role")
        assert result is not None, "Required property 'role' is missing"
        return typing.cast(aws_cdk.aws_iam.IRole, result)

    @builtins.property
    def service_namespace(self) -> ServiceNamespace:
        '''Service namespace of the scalable attribute.'''
        result = self._values.get("service_namespace")
        assert result is not None, "Required property 'service_namespace' is missing"
        return typing.cast(ServiceNamespace, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "BaseScalableAttributeProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "AdjustmentTier",
    "AdjustmentType",
    "BaseScalableAttribute",
    "BaseScalableAttributeProps",
    "BaseTargetTrackingProps",
    "BasicStepScalingPolicyProps",
    "BasicTargetTrackingScalingPolicyProps",
    "CfnScalableTarget",
    "CfnScalableTargetProps",
    "CfnScalingPolicy",
    "CfnScalingPolicyProps",
    "CronOptions",
    "EnableScalingProps",
    "IScalableTarget",
    "MetricAggregationType",
    "PredefinedMetric",
    "ScalableTarget",
    "ScalableTargetProps",
    "ScalingInterval",
    "ScalingSchedule",
    "Schedule",
    "ServiceNamespace",
    "StepScalingAction",
    "StepScalingActionProps",
    "StepScalingPolicy",
    "StepScalingPolicyProps",
    "TargetTrackingScalingPolicy",
    "TargetTrackingScalingPolicyProps",
]

publication.publish()
