import time

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

from helpers.core import create_session, get_account_id, get_src_state, add_ssm_params_to_state
from helpers.dependencies import RESOURCE_DEPENDENCIES



"""
Function to create all AWS resources needed by CloudCopyCat,
in both source and destination accounts

Source account actions performed:
    - Get list of all buckets to copy data from
    - Update bucket policies to allow Batch Copy IAM role to get objects
    - Enable bucket versioning if not already - determine how to copy objects with null versionID
    - Update KMS key (policy) encrypting bucket to allow Batch Copy IAM role decryption
    - Create Inventory Report configurations on buckets, sent to destination bucket

Destination account actions performed:
    - Create KMS CMK for encrypting all data at rest
    - Create SNS topic for email notifications regarding status
    - Create S3 bucket where copied objects will be stored
    - Create Lambda state file in S3 bucket
    - Create IAM roles for Batch Copy actions and Lambda
    - Create SSM parameters to hold values required by Lambda (instead of env vars)
    - Create Lambda to track completion state
    - Create EB rule to trigger Lambda when Inventory Report manifest is uploaded to destination bucket
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
        print("No source buckets to copy data from, exiting.")
        return
    
    param_data = get_param_data(src_account_id, dest_account_id)
    add_ssm_params_to_state(state, param_data)
    state["src_account"] = src_account_id
    state["dest_account"] = dest_account_id
    state["iam"] = {}

    aws_resources = [
        dest_kms_key(src_account_id, args.dest_bucket),
        dest_bucket(args.dest_bucket, dest_account_id),
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
        ## TODO
        #src_batch_replication(bucket_names)
    ]

    ## Declare number of resources for each ResourceGroup
    num_resources = {
        "src_bucket": {},
        "src_kms_key": {},
        "dest_ssm_param": {}
    }
    for region in regions:
        num_resources["src_bucket"][region] = len(state[region]["src_bucket"])
        num_resources["src_kms_key"][region] = len(state[region]["src_kms_key"])
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
        print("Removing deployment")
        cloudcopycat.delete()
    else:
        print("Creating new deployment")
        cloudcopycat.create()



    # src_region_dict = get_src_buckets(src_session, args.region)
    # num_regions = len(src_region_dict.keys())

    # ## create keys in every region first, all ARNs needed for global IAM policy
    # dest_kms_dict = {"all_arn": []}
    # for region in src_region_dict.keys():
    #     src_session = create_session(args.src_profile, region=region)
    #     dest_session = create_session(args.dest_profile, region=region)
    #     dest_bucket = args.dest_bucket
    #     if num_regions > 1:
    #         dest_bucket = f"{dest_bucket}-{region}"
    #     src_buckets = src_region_dict[region]["buckets"]

    #     ## type(kms) == {"arn": str, "id": str}
    #     kms = create_dest_key(
    #             dest_session,
    #             src_account_id,
    #             dest_account_id,
    #             src_buckets,
    #             dest_bucket
    #         )
    #     dest_kms_dict["all_arn"].append(kms["arn"])
    #     dest_kms_dict[region] = kms

    # all_src_kms_arns = []
    # all_dest_buckets = []
    # for region in src_region_dict.keys():
    #     all_src_kms_arns += src_region_dict[region]["kms"]
    # ## Create roles once for all regions
    # ## type(roles) == {rolename => role ARN str}
    # roles = create_iam_roles(
    #             src_session,
    #             dest_session,
    #             src_buckets,
    #             all_src_kms_arns, ## TODO if this is empty, remove IAM statement
    #             dest_account_id,
    #             dest_bucket,
    #             dest_kms_dict["all_arn"]
    #         )
    # ## ensure roles are fully created before proceeding
    # time.sleep(10)


    # for region in src_region_dict.keys():
    #     src_session = create_session(args.src_profile, region=region)
    #     dest_session = create_session(args.dest_profile, region=region)
    #     dest_bucket = args.dest_bucket
    #     if num_regions > 1:
    #         dest_bucket = f"{dest_bucket}-{region}"
    #     src_buckets = src_region_dict[region]["buckets"]
    #     src_kms_arns = src_region_dict[region]["kms"]

    #     create_sns_topic(
    #         dest_session,
    #         dest_kms_dict[region]["id"],
    #         args.email
    #     )
    #     create_dest_bucket(
    #         dest_session,
    #         dest_kms_dict[region]["arn"],
    #         dest_bucket
    #     )
    #     create_state_object(
    #         dest_session,
    #         src_buckets,
    #         dest_bucket
    #     )
    #     add_dest_bucket_policy(
    #         dest_session,
    #         src_buckets,
    #         src_account_id,
    #         dest_bucket,
    #         roles[REPLICATION_ROLE_NAME]
    #     )

    #     ssm_params = [
    #         {
    #             "Name": "CloudCopyCat-Source-Account-ID",
    #             "Value": src_account_id
    #         },
    #         {
    #             "Name": "CloudCopyCat-State-File-Path",
    #             "Value": f"{LAMBDA_STATE_FOLDER}/{LAMBDA_STATE_FILE_NAME}"
    #         },
    #         {
    #             "Name": "CloudCopyCat-Batch-Copy-Role-Arn",
    #             "Value": f"arn:aws:iam::{dest_account_id}:role/{BATCH_COPY_ROLE_NAME}"
    #         }
    #     ]
    #     create_ssm_params(
    #         dest_session,
    #         ssm_params,
    #         dest_kms_dict[region]["id"]
    #     )

    #     ## type(lambda_arn) == str
    #     lambda_arn = create_lambda(
    #         dest_session,
    #         roles[LAMBDA_ROLE_NAME],
    #         dest_bucket,
    #         dest_kms_dict[region]["arn"]
    #     )
    #     ## lambda needs to be created before batch replication occurs
    #     time.sleep(20)

    #     ## type(rule_arn) == str
    #     rule_arn = create_eb_rule(
    #         dest_session,
    #         lambda_arn,
    #         dest_bucket
    #     )
    #     add_lambda_permission(
    #         dest_session,
    #         rule_arn,
    #         dest_account_id
    #     )

    #     update_src_keys(
    #         src_session,
    #         src_region_dict[region]["kms"],
    #         roles[BATCH_COPY_ROLE_NAME]
    #     )

    #     update_src_bucket_policies(
    #         src_session,
    #         src_buckets,
    #         roles[BATCH_COPY_ROLE_NAME]
    #     )
    #     enable_bucket_versioning(
    #         src_session,
    #         src_buckets
    #     )
    #     enable_s3_replication(
    #         src_session,
    #         src_buckets,
    #         dest_account_id,
    #         dest_bucket,
    #         roles[REPLICATION_ROLE_NAME],
    #         dest_kms_dict[region]["arn"]
    #     )
    #     create_batch_replication_jobs(
    #         src_session,
    #         src_account_id,
    #         src_buckets,
    #         dest_account_id,
    #         dest_bucket,
    #         roles[REPLICATION_ROLE_NAME],
    #         dest_kms_dict[region]["arn"]
    #     )
    # return