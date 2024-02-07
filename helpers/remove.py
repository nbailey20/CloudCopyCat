from modules.sts import create_session
from modules.kms import delete_kms_key
from modules.sns import delete_sns_topic
from modules.s3 import get_buckets, delete_bucket# remove replication
from modules.iam import delete_iam_roles
from modules.eventbridge import delete_eb_rule
from modules.lambda_func import delete_lambda
from modules.ssm_parameter import delete_ssm_params



def delete_resources(args):
    src_session = create_session(args.src_profile)
    source_bucket_dict = get_buckets(src_session, args.region)

    for region in source_bucket_dict.keys(): ## limit for testing
        src_session = create_session(args.src_profile, region=region)
        dest_session = create_session(args.dest_profile, region=region)
        ssm_params = [
            "CloudCopyCat-Source-Account-ID",
            "CloudCopyCat-State-File-Path",
            "CloudCopyCat-Batch-Role-Arn"
        ]

        delete_eb_rule(dest_session)
        delete_lambda(dest_session)
        delete_ssm_params(dest_session, ssm_params)
        delete_iam_roles(src_session, dest_session)
        delete_sns_topic(dest_session)
        delete_kms_key(dest_session)

        ## add step to remove statement from source bucket policies

        ## Print status for confirmation
        # state = get_state_object(dp)
        # display_status(state)

        #delete_bucket(dest_session, args.dest_bucket)
    return