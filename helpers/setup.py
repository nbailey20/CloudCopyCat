import time

from helpers.config import LAMBDA_STATE_FOLDER, LAMBDA_STATE_FILE_NAME
from helpers.config import LAMBDA_ROLE_NAME, REPLICATION_ROLE_NAME, BATCH_COPY_ROLE_NAME

from modules.sts import get_account_id, create_session
from modules.kms import create_kms_key
from modules.sns import create_sns_topic
from modules.s3 import get_buckets, create_bucket, add_dest_bucket_policy, update_src_bucket_policies, create_state_object
from modules.s3 import enable_bucket_versioning, enable_s3_replication, create_batch_replication_jobs
from modules.iam import create_iam_roles
from modules.lambda_func import create_lambda, add_lambda_permission
from modules.ssm_parameter import create_ssm_params
from modules.eventbridge import create_eb_rule

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


def create_resources(args):
    src_account_id = get_account_id(args.src_profile)
    dest_account_id = get_account_id(args.dest_profile)

    ## need to use us-east-1 to list all buckets
    src_session = create_session(args.src_profile)
    dest_session = create_session(args.dest_profile, region=args.region)
    source_buckets, source_region_dict = get_buckets(src_session, args.region)

    ## type(kms) == {"arn": str, "id": str}
    kms = create_kms_key(
            dest_session,
            src_account_id,
            dest_account_id,
            source_buckets,
            args.dest_bucket
        )

    ## type(roles) == {rolename => str}
    roles = create_iam_roles(
                src_session,
                dest_session,
                source_buckets,
                dest_account_id,
                args.dest_bucket,
                kms["arn"]
            )
    ## ensure roles are fully created before proceeding
    time.sleep(10)

    create_sns_topic(
        dest_session,
        kms["id"],
        args.email
    )
    create_bucket(
        dest_session,
        kms["arn"],
        args.dest_bucket
    )
    create_state_object(
        dest_session,
        source_buckets,
        args.dest_bucket
    )
    add_dest_bucket_policy(
        dest_session,
        source_buckets,
        src_account_id,
        args.dest_bucket,
        roles[REPLICATION_ROLE_NAME]
    )

    ssm_params = [
        {
            "Name": "CloudCopyCat-Source-Account-ID",
            "Value": src_account_id
        },
        {
            "Name": "CloudCopyCat-State-File-Path",
            "Value": f"{LAMBDA_STATE_FOLDER}/{LAMBDA_STATE_FILE_NAME}"
        },
        {
            "Name": "CloudCopyCat-Batch-Copy-Role-Arn",
            "Value": f"arn:aws:iam::{dest_account_id}:role/{BATCH_COPY_ROLE_NAME}"
        }
    ]
    create_ssm_params(
        dest_session,
        ssm_params,
        kms["id"]
    )

    ## type(lambda_arn) == str
    lambda_arn = create_lambda(
        dest_session,
        roles[LAMBDA_ROLE_NAME],
        args.dest_bucket,
        kms["arn"]
    )
    ## lambda needs to be created before batch replication occurs
    time.sleep(20)

    ## type(rule_arn) == str
    rule_arn = create_eb_rule(
        dest_session,
        lambda_arn,
        args.dest_bucket
    )
    add_lambda_permission(
        dest_session,
        rule_arn,
        dest_account_id
    )

    for region in source_region_dict.keys():
        src_session = create_session(args.src_profile, region=region)

        update_src_bucket_policies(
            src_session,
            source_region_dict[region],
            roles[BATCH_COPY_ROLE_NAME]
        )
        enable_bucket_versioning(
            src_session,
            source_region_dict[region]
        )
        enable_s3_replication(
            src_session,
            source_region_dict[region],
            dest_account_id,
            args.dest_bucket,
            roles[REPLICATION_ROLE_NAME],
            kms["arn"]
        )
        create_batch_replication_jobs(
            src_session,
            src_account_id,
            source_region_dict[region],
            dest_account_id,
            args.dest_bucket,
            roles[REPLICATION_ROLE_NAME],
            kms["arn"]
        )
    return