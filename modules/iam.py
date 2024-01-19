import json

from helpers.config import LAMBDA_POLICY_NAME, LAMBDA_ROLE_NAME, LAMBDA_STATE_FILE_PATH
from helpers.config import BATCH_COPY_POLICY_NAME, BATCH_COPY_ROLE_NAME

from resources.iam.lambda_role import LAMBDA_IAM_POLICY_TEMPLATE, LAMBDA_TRUST_POLICY
from resources.iam.batch_copy_role import BATCH_COPY_IAM_POLICY_TEMPLATE, BATCH_COPY_TRUST_POLICY

from modules.sts import get_account_id


def generate_lambda_policy(dest_account_id, dest_bucket_name):
    LAMBDA_IAM_POLICY_TEMPLATE["Statement"][0]["Resource"] = f"arn:aws:logs:*:{dest_account_id}:*"
    LAMBDA_IAM_POLICY_TEMPLATE["Statement"][1]["Resource"] = f"arn:aws:logs:*:{dest_account_id}:log-group:/aws/lambda*"
    LAMBDA_IAM_POLICY_TEMPLATE["Statement"][3]["Resource"] = f"arn:aws:iam::{dest_account_id}:role/{BATCH_COPY_ROLE_NAME}"
    LAMBDA_IAM_POLICY_TEMPLATE["Statement"][5]["Resource"] = f"arn:aws:ssm:*:{dest_account_id}:parameter/CloudCopyCat-*"
    LAMBDA_IAM_POLICY_TEMPLATE["Statement"][6]["Resource"] = f"arn:aws:s3:::{dest_bucket_name}/{LAMBDA_STATE_FILE_PATH}"
    return json.dumps(LAMBDA_IAM_POLICY_TEMPLATE)


def generate_batch_policy(source_buckets, dest_bucket_name):
    source_bucket_arns = [f"arn:aws:s3:::{b}/*" for b in source_buckets]
    dest_bucket_arn = f"arn:aws:s3:::{dest_bucket_name}/*"
    BATCH_COPY_IAM_POLICY_TEMPLATE["Statement"][0]["Resource"] = source_bucket_arns + [dest_bucket_arn]
    BATCH_COPY_IAM_POLICY_TEMPLATE["Statement"][1]["Resource"] = dest_bucket_arn
    return json.dumps(BATCH_COPY_IAM_POLICY_TEMPLATE)


def create_iam_roles(session, source_buckets, dest_account_id, dest_bucket_name):
    client = session.client("iam")

    roles_list = [
        {
            "RoleName":    LAMBDA_ROLE_NAME,
            "PolicyName":  LAMBDA_POLICY_NAME,
            "TrustPolicy": json.dumps(LAMBDA_TRUST_POLICY),
            "IamPolicy":   generate_lambda_policy(dest_account_id, dest_bucket_name)
        },
        {
            "RoleName":    BATCH_COPY_ROLE_NAME,
            "PolicyName":  BATCH_COPY_POLICY_NAME,
            "TrustPolicy": json.dumps(BATCH_COPY_TRUST_POLICY),
            "IamPolicy":   generate_batch_policy(source_buckets, dest_bucket_name)
        }
    ]

    role_arns = {}
    for role in roles_list:
        role_arn = client.create_role(
            RoleName                 = role["RoleName"],
            AssumeRolePolicyDocument = role["TrustPolicy"]
        )["Role"]["Arn"]
        role_arns[role["RoleName"]] = role_arn

        policy_arn = client.create_policy(
            PolicyName     = role["PolicyName"],
            PolicyDocument = role["IamPolicy"]
        )["Policy"]["Arn"]

        client.attach_role_policy(
            RoleName  = role["RoleName"],
            PolicyArn = policy_arn
        )

    return role_arns



def delete_iam_roles(session):
    account_id = get_account_id(session=session)
    client = session.client("iam")

    roles_list = [
        {
            "RoleName":  LAMBDA_ROLE_NAME,
            "PolicyArn": f"arn:aws:iam::{account_id}:policy/{LAMBDA_POLICY_NAME}"
        },
        {
            "RoleName":  BATCH_COPY_ROLE_NAME,
            "PolicyArn": f"arn:aws:iam::{account_id}:policy/{BATCH_COPY_POLICY_NAME}"
        }
    ]

    for role in roles_list:
        client.detach_role_policy(
            RoleName  = role["RoleName"],
            PolicyArn = role["PolicyArn"]
        )
        client.delete_role(
            RoleName = role["RoleName"]
        )
        client.delete_policy(
            PolicyArn = role["PolicyArn"]
        )
    return