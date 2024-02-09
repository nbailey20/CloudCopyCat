import json

from helpers.config import LAMBDA_POLICY_NAME, LAMBDA_ROLE_NAME, LAMBDA_STATE_FOLDER
from helpers.config import REPLICATION_POLICY_NAME, REPLICATION_ROLE_NAME
from helpers.config import BATCH_COPY_POLICY_NAME, BATCH_COPY_ROLE_NAME

from resources.iam.lambda_role import LAMBDA_IAM_POLICY_TEMPLATE, LAMBDA_TRUST_POLICY
from resources.iam.replication_role import REPLICATION_IAM_POLICY_TEMPLATE, REPLICATION_TRUST_POLICY
from resources.iam.batch_copy_role import BATCH_COPY_IAM_POLICY_TEMPLATE, BATCH_COPY_TRUST_POLICY

from modules.sts import get_account_id


def generate_lambda_policy(dest_account_id, dest_bucket_name):
    LAMBDA_IAM_POLICY_TEMPLATE["Statement"][0]["Resource"] = f"arn:aws:logs:*:{dest_account_id}:*"
    LAMBDA_IAM_POLICY_TEMPLATE["Statement"][1]["Resource"] = f"arn:aws:logs:*:{dest_account_id}:log-group:/aws/lambda*"
    LAMBDA_IAM_POLICY_TEMPLATE["Statement"][3]["Resource"] = f"arn:aws:iam::{dest_account_id}:role/{BATCH_COPY_ROLE_NAME}"
    LAMBDA_IAM_POLICY_TEMPLATE["Statement"][5]["Resource"] = f"arn:aws:ssm:*:{dest_account_id}:parameter/CloudCopyCat-*"
    LAMBDA_IAM_POLICY_TEMPLATE["Statement"][6]["Resource"] = f"arn:aws:s3:::{dest_bucket_name}/{LAMBDA_STATE_FOLDER}/*"
    return json.dumps(LAMBDA_IAM_POLICY_TEMPLATE)

def generate_replication_policy(source_buckets, dest_bucket_name):
    source_bucket_arns = [f"arn:aws:s3:::{b}" for b in source_buckets]
    source_object_arns = [f"{sba}/*" for sba in source_bucket_arns]
    dest_object_arn = f"arn:aws:s3:::{dest_bucket_name}/*"
    REPLICATION_IAM_POLICY_TEMPLATE["Statement"][0]["Resource"] = source_object_arns
    REPLICATION_IAM_POLICY_TEMPLATE["Statement"][1]["Resource"] = source_bucket_arns
    REPLICATION_IAM_POLICY_TEMPLATE["Statement"][2]["Resource"] = dest_object_arn
    return json.dumps(REPLICATION_IAM_POLICY_TEMPLATE)

def generate_batch_copy_policy(source_buckets, dest_bucket_name, dest_kms_arn):
    source_bucket_arns = [f"arn:aws:s3:::{b}/*" for b in source_buckets]
    dest_bucket_arn = f"arn:aws:s3:::{dest_bucket_name}/*"
    BATCH_COPY_IAM_POLICY_TEMPLATE["Statement"][0]["Resource"] = source_bucket_arns + [dest_bucket_arn]
    BATCH_COPY_IAM_POLICY_TEMPLATE["Statement"][1]["Resource"] = dest_bucket_arn
    BATCH_COPY_IAM_POLICY_TEMPLATE["Statement"][2]["Resource"] = dest_kms_arn
    return json.dumps(BATCH_COPY_IAM_POLICY_TEMPLATE)


## Create IAM roles and attached policies for Lambda and Batch Copy jobs
def create_iam_roles(src_session, dest_session, source_buckets, dest_account_id, dest_bucket_name, dest_kms_arn):
    roles_list = [
        {
            "RoleName":    LAMBDA_ROLE_NAME,
            "PolicyName":  LAMBDA_POLICY_NAME,
            "TrustPolicy": json.dumps(LAMBDA_TRUST_POLICY),
            "IamPolicy":   generate_lambda_policy(dest_account_id, dest_bucket_name),
            "ApiClient":   dest_session.client("iam")
        },
        {
            "RoleName":    REPLICATION_ROLE_NAME,
            "PolicyName":  REPLICATION_POLICY_NAME,
            "TrustPolicy": json.dumps(REPLICATION_TRUST_POLICY),
            "IamPolicy":   generate_replication_policy(source_buckets, dest_bucket_name),
            "ApiClient":   src_session.client("iam")
        },
        {
            "RoleName":    BATCH_COPY_ROLE_NAME,
            "PolicyName":  BATCH_COPY_POLICY_NAME,
            "TrustPolicy": json.dumps(BATCH_COPY_TRUST_POLICY),
            "IamPolicy":   generate_batch_copy_policy(source_buckets, dest_bucket_name, dest_kms_arn),
            "ApiClient":   dest_session.client("iam")
        }
    ]

    role_arns = {}
    for role in roles_list:
        role_arn = role["ApiClient"].create_role(
            RoleName                 = role["RoleName"],
            AssumeRolePolicyDocument = role["TrustPolicy"]
        )["Role"]["Arn"]
        role_arns[role["RoleName"]] = role_arn

        policy_arn = role["ApiClient"].create_policy(
            PolicyName     = role["PolicyName"],
            PolicyDocument = role["IamPolicy"]
        )["Policy"]["Arn"]

        role["ApiClient"].attach_role_policy(
            RoleName  = role["RoleName"],
            PolicyArn = policy_arn
        )

    return role_arns



def delete_iam_roles(src_session, dest_session):
    src_account_id = get_account_id(session=src_session)
    dest_account_id = get_account_id(session=dest_session)

    roles_list = [
        {
            "RoleName":  LAMBDA_ROLE_NAME,
            "PolicyArn": f"arn:aws:iam::{dest_account_id}:policy/{LAMBDA_POLICY_NAME}",
            "ApiClient": dest_session.client("iam")
        },
        {
            "RoleName":  REPLICATION_ROLE_NAME,
            "PolicyArn": f"arn:aws:iam::{src_account_id}:policy/{REPLICATION_POLICY_NAME}",
            "ApiClient": src_session.client("iam")
        },
        {
            "RoleName":  BATCH_COPY_ROLE_NAME,
            "PolicyArn": f"arn:aws:iam::{dest_account_id}:policy/{BATCH_COPY_POLICY_NAME}",
            "ApiClient": dest_session.client("iam")
        }
    ]

    for role in roles_list:
        role["ApiClient"].detach_role_policy(
            RoleName  = role["RoleName"],
            PolicyArn = role["PolicyArn"]
        )
        role["ApiClient"].delete_role(
            RoleName = role["RoleName"]
        )
        role["ApiClient"].delete_policy(
            PolicyArn = role["PolicyArn"]
        )
    return