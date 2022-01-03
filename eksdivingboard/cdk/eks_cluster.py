from aws_cdk import (
    aws_eks as eks,
)

import logging
from .structures import StackConstruct

logger = logging.getLogger(__name__)


class EKSCluster(StackConstruct):
    def __init__(self, scope, configs):
        super().__init__(scope, configs)
        self.construct_type = 'eks'
        self.base_construct = eks.Cluster

    def set_defaults(self):
        self.configs.setdefault('version', 'v1.21')

    @staticmethod
    def version(version):
        accepted_versions = {
            'v1.18': eks.KubernetesVersion.V1_18,
            'v1.19': eks.KubernetesVersion.V1_19,
            'v1.20': eks.KubernetesVersion.V1_20,
            'v1.21': eks.KubernetesVersion.V1_21,
        }

        try:
            return accepted_versions[version[0:5]]

        except KeyError:
            error_message = "".join([
                f"the EKS cluster version {version} was not found. ",
                f"Valid EKS platform versions are: {accepted_versions.keys()}.",
            ])
            raise ValueError(error_message)
