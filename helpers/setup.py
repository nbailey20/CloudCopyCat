import time

from helpers.config import LAMBDA_STATE_FILE_PATH, BATCH_COPY_ROLE_NAME

from modules.sts import get_account_id, create_session
from modules.kms import create_kms_key
from modules.sns import create_sns_topic
from modules.s3 import get_buckets, create_bucket, add_bucket_policies, create_state_object, create_inv_configs
from modules.iam import create_iam_roles
from modules.lambda_func import create_lambda, add_lambda_permission
from modules.ssm_parameter import create_ssm_params
from modules.eventbridge import create_eb_rule



def create_resources(args):
    src_account_id = get_account_id(args.src_profile)
    dest_account_id = get_account_id(args.dest_profile)

    src_session = create_session(args.src_profile)
    source_bucket_dict = get_buckets(src_session, args.region)

    for region in source_bucket_dict.keys():
        src_session = create_session(args.src_profile, region=region)
        dest_session = create_session(args.dest_profile, region=region)
        ssm_params = [
            {
                "Name": "CloudCopyCat-Source-Account-ID",
                "Value": src_account_id
            },
            {
                "Name": "CloudCopyCat-State-File-Path",
                "Value": LAMBDA_STATE_FILE_PATH
            },
            {
                "Name": "CloudCopyCat-Batch-Role-Arn",
                "Value": f"arn:aws:iam::{dest_account_id}:role/{BATCH_COPY_ROLE_NAME}"
            },
        ]

        kms = #create_kms_key(dest_session, src_account_id, dest_account_id, source_bucket_dict[region])
        # create_sns_topic(dest_session, kms["id"], args.email)
        # create_bucket(dest_session, region, kms["id"], args.dest_bucket)
        roles = create_iam_roles(dest_session, source_bucket_dict[region], dest_account_id, args.dest_bucket)
        time.sleep(5)
        lambda_arn = create_lambda(dest_session, roles, args.dest_bucket, kms["arn"])
        create_ssm_params(dest_session, ssm_params, kms["id"])
        rule_arn = create_eb_rule(dest_session, lambda_arn, args.dest_bucket)
        add_lambda_permission(dest_session, rule_arn)
        add_bucket_policies(dest_session, source_bucket_dict[region], src_account_id, args.dest_bucket, roles[BATCH_COPY_ROLE_NAME])
        create_state_object(src_session, dest_session, source_bucket_dict[region], args.dest_bucket)
        create_inv_configs(src_session, source_bucket_dict[region], dest_account_id, args.dest_bucket)

    return