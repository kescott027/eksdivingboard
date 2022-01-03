from aws_cdk import (
    core as cdk,
    aws_ec2 as ec2,
    aws_eks as eks,
    aws_iam as iam,
)

import logging

logger = logging.getLogger(__name__)


class EksCluster(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        base_cluster_iam_role = iam.Role(
            self,
            'base_cluster_iam_role',
            assumed_by=iam.AccountRootPrincipal()
        )

        base_eks_cluster = eks.FargateCluster(
            self,
            'base_eks_cluster',
            version=eks.KubernetesVersion.V1_21,
            masters_role=base_cluster_iam_role,
            cluster_name='EKSdiveCluster',
            output_cluster_name=True,
            endpoint_access=eks.EndpointAccess.PUBLIC,
            vpc=ec2.Vpc.fromLookup(
                self,
                'vpc',
                vpc_id='vpc-009508920dc9df9d3'
            )
        )

