from aws_cdk import (
    core as cdk,
    aws_ec2 as ec2,
    aws_logs as logs,
)

from structures import StackConstruct


class AwsVpc(StackConstruct):
    def __init__(self, scope, id, cidr="10.0.0.0/16", **kwargs):
        super().__init__(scope, id, **kwargs)
        self._required_args = ['cidr']
        self.cidr = None
        self.base_construct = ec2.Vpc

    @staticmethod
    def default_instance_tenancy(string_value):
        return getattr(ec2.DefaultInstanceTenancy, string_value.upper())

    def flow_logs(self, destination=None, traffic_type=None):
        def _to_cloud_watch_logs(**kwargs):
            log_group = None
            iam_role = None
            if 'log_group' in destination['to_cloud_watch_logs'].keys():
                log_group = logs.LogGroup(
                    scope=self.scope,
                    id=destination[
                           'to_cloud_watch_logs'][
                           'log_group'].pop(
                        'log_group_name') + 'flow_log_group',
                    **destination['to_cloud_watch_logs']['log_group']
                )
            cloud_watch_logs_params = {
                'log_group': log_group,
                'iam_role': iam_role
            }
            destination_params['destination'] = ec2.FlowLogOptions(**cloud_watch_logs_params)

        params = {}
        if destination:
            destination_params = {}
            if type(destination, dict):
                # TODO: Complete this
                if 'to_cloud_watch_logs' in destination.keys():
                    nothing = None
                if 'to_s3' in destination.keys():
                    bucket = None



        if traffic_type:
            params['traffic_type'] = None
        return getattr(**params)

