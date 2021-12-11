from aws_cdk import (
    aws_eks as eks,
    core as cdk
)


class EKSCluster(cdk.Construct):
    def __init__(self, scope, id, cluster_name, kubernetes_version=None):
        super().__init__(scope, id)
        self._cluster_name = cluster_name
        self._cluster_version = self._set_cluster_version(kubernetes_version)
        self._create_resource()

    def _create_resource(self):
        self.cluster = eks.Cluster(
            scope=self,
            id=self._cluster_name,
            version=self._cluster_version
        )

    @staticmethod
    def _set_cluster_version(version=None):
        version = 'v1.21' if not version else version
        accepted_versions = {
            'v1.18': eks.KubernetesVersion.V1_18,
            'v1.19': eks.KubernetesVersion.V1_19,
            'v1.20': eks.KubernetesVersion.V1_20,
            'v1.21': eks.KubernetesVersion.V1_21,
        }

        truncated_version = version[0:5]
        try:
            return accepted_versions[truncated_version]

        except KeyError:
            error_message = "".join([
                f"the EKS cluster version {version} was not found. ",
                f"Valid EKS platform versions are: {accepted_versions.keys()}.",
            ])
            raise ValueError(error_message)
