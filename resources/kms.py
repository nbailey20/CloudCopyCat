import json
from classes.ApiCall import ApiCall
from classes.Resource import Resource
from classes.ResourceGroup import ResourceGroup
from classes.Transformer import Transformer
from configs.kms.source_key import SOURCE_KMS_POLICY_TEMPLATE
from configs.kms.dest_key import DEST_KMS_POLICY_TEMPLATE
from helpers.config import KMS_ALIAS_NAME, REPLICATION_ROLE_NAME

## DEST KEY
def dest_kms_key(src_account, bucket_name, multi_region=False):
    if multi_region:
        bucket_name = f"{bucket_name}-${{region}}"
    ## creation APIs
    def update_key_condition(
            policy: dict=None,
            src_bucket_arns: str=None,
            dest_bucket_arn: str=None,
            role_arn: str=None
        ):
        statements = policy["Statement"]
        statements[1]["Condition"]["ArnLike"]["aws:SourceArn"] = json.loads(src_bucket_arns) + [dest_bucket_arn]
        statements[2]["Condition"]["StringEquals"]["aws:PrincipalArn"] = role_arn
        return {"policy": json.dumps(policy)}
    generate_policy = Transformer(
        func = update_key_condition,
        function_args = {
            "policy": DEST_KMS_POLICY_TEMPLATE,
            "src_bucket_arns": "$src_bucket/#all/arn",
            "dest_bucket_arn": f"arn:aws:s3:::{bucket_name}",
            "role_arn": f"arn:aws:iam::{src_account}:role/{REPLICATION_ROLE_NAME}"
        },
        output_keys = ["policy"]
    )
    key_create = ApiCall(
        method = "create_key",
        method_args = {
            "Policy": "$dest_kms_key/policy"
        },
        output_keys = {
            "arn": "KeyMetadata/Arn",
            "id": "KeyMetadata/KeyId"
        }
    )
    alias_create = ApiCall(
        method = "create_alias",
        method_args = {
            "AliasName": f"alias/{KMS_ALIAS_NAME}",
            "TargetKeyId": "$dest_kms_key/arn"
        }
    )


    ## description APIs
    key_describe = ApiCall(
        method = "list_aliases",
        output_keys = {
            "id": f"Aliases/?/AliasName~{KMS_ALIAS_NAME}/TargetKeyId"
        }
    )
    get_arn = ApiCall(
        method = "describe_key",
        method_args = {"KeyId": "$dest_kms_key/id"},
        output_keys = {"arn": "KeyMetadata/Arn"}
    )
    


    ## deletion APIs
    alias_delete = ApiCall(
        method = "delete_alias",
        method_args = {
            "AliasName": f"alias/{KMS_ALIAS_NAME}"
        }
    )
    key_delete = ApiCall(
        method = "schedule_key_deletion",
        method_args = {
            "KeyId": "$dest_kms_key/arn",
            "PendingWindowInDays": 7
        }
    )

    kms_resource = Resource(
        name = "dest_kms_key",
        type = "kms",
        create_apis = (generate_policy, key_create, alias_create),
        describe_apis = (key_describe, get_arn),
        delete_apis = (alias_delete, key_delete)
    )
    return kms_resource



## SOURCE KEYS
def src_kms_key():
    set_policy = ApiCall(
        method = "put_key_policy",
        method_args = {
            "KeyId": "$src_kms_key/#id/id",
            "Policy": "$src_kms_key/#id/policy",
            "PolicyName": "default"
        }
    )

    ## Create API
    def append_statements(policy=None):
        if not policy:
            return {"policy": None}
        policy = json.loads(policy)
        policy["Statement"].append(SOURCE_KMS_POLICY_TEMPLATE)
        return {"policy": json.dumps(policy)}
    update_policy = Transformer(
        func = append_statements,
        function_args = {"policy": "$src_kms_key/#id/policy"},
        output_keys = ["policy"]
    )


    ## Describe API
    get_policy = ApiCall(
        method = "get_key_policy",
        method_args = {"KeyId": "$src_kms_key/#id/arn", "PolicyName": "default"},
        output_keys = {"policy": "Policy"}
    )
    def search_for_sid(policy=None):
        if policy == "null":
            return {"arn": None}
        policy = json.loads(policy)
        for statement in policy["Statement"]:
            if "Sid" in statement and "CloudCopyCat" in statement["Sid"]:
                return {"arn": f"arn:aws:kms:$region:$src_account:key/$src_kms_key/#id/id"}
        return {"arn": None}
    validate_policy = Transformer(
        func = search_for_sid,
        function_args = {"policy": "$src_kms_key/#id/policy"},
        output_keys = ["arn"]
    )


    ## Delete API
    def remove_statements(policy=None):
        if not policy:
            return {"policy": None}
        policy = json.loads(policy)
        statements = policy["Statement"]
        for statement in statements:
            if "Sid" in statement and "CloudCopyCat" in statement["Sid"]:
                statements.remove(statement)
        return {"policy": json.dumps(policy)}
    revert_policy = Transformer(
        func = remove_statements,
        function_args = {"policy": "$src_kms_key/#id/policy"},
        output_keys = ["policy"]
    )

    kms_resource = ResourceGroup(
        name = "src_kms_key",
        type = "kms",
        create_apis = (update_policy, set_policy),
        describe_apis = (get_policy, validate_policy),
        delete_apis = (revert_policy, set_policy)
    )
    return kms_resource