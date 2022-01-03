from eksdivingboard.cdk import compiler
from eksdivingboard.cdk import eks_cluster
from eksdivingboard.cdk import infrastructure_stack
from eksdivingboard.cdk import structures
from eksdivingboard.cdk import vpc
import logging

logger = logging.getLogger('eks_diving_board')
logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)
