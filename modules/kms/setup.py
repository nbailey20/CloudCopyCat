from helpers.config import KMS_ALIAS_NAME
from modules.kms.helpers import generate_dest_policies, generate_src_policies


## Create KMS CMK and alias with appropriate key policy
## Return key ID and ARN as a string dict
def create_dest_keys(session, src_account_id, dest_account_id, src_buckets, dest_bucket):
    kms_policy = generate_dest_policies(src_account_id, dest_account_id, src_buckets, dest_bucket)
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



def update_src_keys(session, src_key_arns, batch_copy_role_arn):
    kms_policies = generate_src_policies(session, src_key_arns, batch_copy_role_arn, revert=False)
    client = session.client("kms")

    for idx, kms_arn in enumerate(src_key_arns):
        client.put_key_policy(
            KeyId      = kms_arn,
            PolicyName = "default",
            Policy     = kms_policies[idx]
        )
    return