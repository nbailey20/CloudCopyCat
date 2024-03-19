from classes.Deployment import Deployment
from resources.kms import dest_kms_key, src_kms_key
from resources.iam import dest_copy_role, dest_copy_policy
from resources.iam import dest_lambda_role, dest_lambda_policy
from resources.iam import src_replication_role, src_replication_policy
from resources.sns import dest_sns_topic
from resources.dest_s3 import dest_bucket
from resources.ssm_parameter import get_param_data, dest_ssm_param
from resources.lambda_func import dest_lambda_function
from resources.eventbridge import dest_eventbridge_rule
from resources.src_s3 import src_bucket
from resources.batch_replication import src_batch_replication

from helpers.core import create_session, get_account_id, get_src_state, add_ssm_params_to_state
from helpers.dependencies import RESOURCE_DEPENDENCIES
from helpers.log import logger



"""
Function to manage all AWS resources needed by CloudCopyCat,
in both source and destination accounts

Source account actions performed:
    - Get list of all buckets to copy data from
    - Update bucket policies to allow Batch Copy IAM role to get objects
    - Enable bucket versioning if not already
    - Update all KMS key policies encrypting buckets to allow Batch Copy IAM role decryption
    - Create Batch Replication jobs for each buckets to generate manifest of objects to copy

Destination account actions performed in each region (except IAM):
    - Create KMS CMK for encrypting all data at rest
    - Create SNS topic for email notifications regarding status
    - Create S3 bucket where copied objects will be stored
    - Create Lambda state file in S3 bucket
    - Create IAM roles for Batch Copy, Replication actions and Lambda
    - Create SSM parameters to hold values required by Lambda (instead of env vars)
    - Create Lambda to track completion state and trigger Batch Copy jobs
    - Create EB rule to trigger Lambda when Batch Replication manifest is uploaded to destination bucket
"""


def run(args):
    src_account_id = get_account_id(args.src_profile)
    dest_account_id = get_account_id(args.dest_profile)
    region_filter = args.region
    if args.region == "*":
        region_filter = None

    ## initial state includes src kms, src buckets, dest ssm params that should be included in deployment
    ## need to use us-east-1 to list all buckets
    src_session = create_session(args.src_profile, region="us-east-1")
    state, regions = get_src_state(src_session, region_filter)
    if not state:
        logger.info("No source buckets to copy data from, exiting.")
        return
    multi_region = False
    if len(regions) > 1:
        multi_region = True
    
    param_data = get_param_data(src_account_id, dest_account_id)
    add_ssm_params_to_state(state, param_data)
    state["src_account"] = src_account_id
    state["dest_account"] = dest_account_id
    state["iam"] = {}

    aws_resources = [
        dest_kms_key(src_account_id, args.dest_bucket, multi_region),
        dest_bucket(args.dest_bucket, multi_region),
        dest_copy_role(),
        dest_copy_policy(),
        dest_lambda_role(),
        dest_lambda_policy(),
        src_replication_role(),
        src_replication_policy(),
        dest_sns_topic(args.email),
        dest_ssm_param(),
        dest_lambda_function(dest_account_id),
        dest_eventbridge_rule(),
        src_kms_key(),
        src_bucket(),
        src_batch_replication(args.force)
    ]

    ## Declare number of resources for each ResourceGroup
    num_resources = {
        "src_bucket": {},
        "src_kms_key": {},
        "src_batch_replication": {},
        "dest_ssm_param": {}
    }
    for region in regions:
        num_resources["src_bucket"][region] = len(state[region]["src_bucket"])
        num_resources["src_kms_key"][region] = len(state[region]["src_kms_key"])
        ## one batch rep job per bucket
        num_resources["src_batch_replication"][region] = len(state[region]["src_bucket"])
        num_resources["dest_ssm_param"][region] = len(state[region]["dest_ssm_param"])


    cloudcopycat = Deployment(
        src_profile = args.src_profile,
        dest_profile = args.dest_profile,
        regions = regions,
        resources = aws_resources,
        num_resources = num_resources,
        dependencies = RESOURCE_DEPENDENCIES,
        state = state
    )

    if args.remove:
        logger.info("Removing deployment")
        cloudcopycat.delete()
    else:
        logger.info("Creating new deployment")
        cloudcopycat.create()
