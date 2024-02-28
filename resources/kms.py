import json
from classes.ApiCall import ApiCall
from classes.Resource import Resource
from configs.kms.source_key import SOURCE_KMS_POLICY_TEMPLATE
from configs.kms.dest_key import DEST_KMS_POLICY_TEMPLATE
from helpers.config import DESCRIPTION, KMS_ALIAS_NAME

## DEST KEY
## creation APIs
dest_key_create = ApiCall(
    method = "create_key",
    method_args = {
        "Policy": json.dumps(DEST_KMS_POLICY_TEMPLATE),
        "Description": DESCRIPTION
    },
    output_keys = {
        "arn": "KeyMetadata/Arn",
        "id": "KeyMetadata/KeyId"
    }
)

dest_alias_create = ApiCall(
    method = "create_alias",
    method_args = {
        "AliasName": KMS_ALIAS_NAME,
        "TargetKeyId": "$dest_kms_key/arn"
    }
)


## description APIs
dest_key_describe = ApiCall(
    method = "list_aliases",
    output_keys = {
        "arn": f"Aliases/?/AliasName~{KMS_ALIAS_NAME}/TargetKeyId"
    }
)


## deletion APIs
dest_alias_delete = ApiCall(
    method = "delete_alias",
    method_args = {
        "AliasName": KMS_ALIAS_NAME
    }
)

dest_key_delete = ApiCall(
    method = "schedule_key_deletion",
    method_args = {
        "KeyId": "$dest_kms_key/arn",
        "PendingWindowInDays": 7
    }
)



## SOURCE KEYS
## creation API
source_key_update = ApiCall(
    method = "put_key_policy",
    method_args = {
        "KeyId": "$source_kms_key/#id/arn"
    }
)