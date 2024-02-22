import json
import copy

from helpers.config import REPLICATION_ROLE_NAME
from resources.kms.dest_key import DEST_KMS_POLICY_TEMPLATE
from resources.kms.source_key import SOURCE_KMS_POLICY_TEMPLATE


def get_kms_policy(session, kms_arn):
    client = session.client("kms")

    policy = client.get_key_policy(
        KeyId      = kms_arn,
        PolicyName = "default"
    )["Policy"]
    return json.loads(policy)


## Statement 0 - default root permissions
## Statement 1 - allow S3 to put inv report if originating from expected buckets in source account
def generate_dest_policies(src_account_id, dest_account_id, src_buckets, dest_bucket):
    DEST_KMS_POLICY_TEMPLATE["Statement"][0]["Principal"]["AWS"] = f"arn:aws:iam::{dest_account_id}:root"
    DEST_KMS_POLICY_TEMPLATE["Statement"][1]["Condition"]["StringEquals"]["aws:SourceAccount"] = [src_account_id, dest_account_id]
    src_bucket_arns = [f"arn:aws:s3:::{b}" for b in src_buckets]
    DEST_KMS_POLICY_TEMPLATE["Statement"][1]["Condition"]["ArnLike"]["aws:SourceArn"] = src_bucket_arns + [f"arn:aws:s3:::{dest_bucket}"]
    DEST_KMS_POLICY_TEMPLATE["Statement"][2]["Condition"]["StringEquals"]["aws:PrincipalArn"] = f"arn:aws:iam::{src_account_id}:role/{REPLICATION_ROLE_NAME}"
    return DEST_KMS_POLICY_TEMPLATE


def generate_src_policies(session, src_key_arns, batch_copy_role_arn, revert):
    policies = []
    for kms_arn in src_key_arns:
        template = copy.deepcopy(SOURCE_KMS_POLICY_TEMPLATE)
        ## don't overwrite existing KMS policies
        ## add/remove an additional statement if revert is False/True
        policy = get_kms_policy(session, kms_arn)
        statements = policy["Statement"]

        if revert:
            for statement in statements:
                if "Sid" in statement and "CloudCopyCat" in statement["Sid"]:
                    statements.remove(statement)
        else:
            template["Principal"]["AWS"] = batch_copy_role_arn
            statements.append(
                template
            )
        policies.append(json.dumps(policy))
    return policies