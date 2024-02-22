from helpers.config import KMS_ALIAS_NAME
from modules.kms.helpers import generate_src_policies


def delete_dest_key(session):
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


def revert_src_keys(session, src_key_arns):
    kms_policies = generate_src_policies(session, src_key_arns, None, revert=True)
    client = session.client("kms")

    for idx, kms_arn in enumerate(src_key_arns):
        client.put_key_policy(
            KeyId      = kms_arn,
            PolicyName = "default",
            Policy     = kms_policies[idx]
        )
    return