import json

from helpers.config import KMS_ALIAS_NAME, REPLICATION_ROLE_NAME
from resources.kms.key import KMS_POLICY_TEMPLATE


## Statement 0 - default root permissions
## Statement 1 - allow S3 to put inv report if originating from expected buckets in source account
def generate_kms_policy(src_account_id, dest_account_id, buckets):
    KMS_POLICY_TEMPLATE["Statement"][0]["Principal"]["AWS"] = f"arn:aws:iam::{dest_account_id}:root"
    KMS_POLICY_TEMPLATE["Statement"][1]["Condition"]["StringEquals"]["aws:SourceAccount"] = src_account_id
    bucket_arns = [f"arn:aws:s3:::{b}" for b in buckets]
    KMS_POLICY_TEMPLATE["Statement"][1]["Condition"]["ArnLike"]["aws:SourceArn"] = bucket_arns
    KMS_POLICY_TEMPLATE["Statement"][2]["Principal"]["AWS"] = f"arn:aws:iam::{src_account_id}:role/{REPLICATION_ROLE_NAME}"
    return json.dumps(KMS_POLICY_TEMPLATE)


## Create KMS CMK and alias with appropriate key policy
## Return key ID and ARN as a string dict
def create_kms_key(session, src_account_id, dest_account_id, buckets):
    kms_policy = generate_kms_policy(src_account_id, dest_account_id, buckets)
    client = session.client("kms")

    kms_data = client.create_key(
        KeyUsage = "ENCRYPT_DECRYPT",
        KeySpec  = "SYMMETRIC_DEFAULT",
        Policy   = kms_policy
    )["KeyMetadata"]

    client.create_alias(
        AliasName   = KMS_ALIAS_NAME,
        TargetKeyId = kms_data["KeyId"]
    )

    return {"id": kms_data["KeyId"], "arn": kms_data["Arn"]}



def delete_kms_key(session):
    client = session.client("kms")
    all_aliases = client.list_aliases()["Aliases"]

    kms_id = [a["TargetKeyId"] for a in all_aliases
                if KMS_ALIAS_NAME == a["AliasName"]]
    if not kms_id:
        return
    kms_id = kms_id[0]

    client.delete_alias(
        AliasName = KMS_ALIAS_NAME
    )
    client.schedule_key_deletion(
        KeyId               = kms_id,
        PendingWindowInDays = 7
    )
    return