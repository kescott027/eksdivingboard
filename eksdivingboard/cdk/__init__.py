import os
import sys
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../')
sys.path.append(BASE_DIR)
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
