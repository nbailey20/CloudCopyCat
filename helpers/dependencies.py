## implied dependencies that don't have to be listed below:
## $src_account
## $dest_account
## $src_bucket
## $src_kms_key
RESOURCE_DEPENDENCIES = {
    "dest_kms_key": [],
    "dest_bucket": [
        "dest_kms_key"
    ],
    "dest_copy_role": [],
    "dest_copy_policy": [
        "dest_copy_role",
        "dest_kms_key",
        "dest_bucket"
    ],
    "dest_lambda_role": [],
    "dest_lambda_policy": [
        "dest_lambda_role",
        "dest_copy_role",
        "dest_kms_key",
        "dest_bucket"
    ],
    "src_replication_role": [],
    "src_replication_policy": [
        "src_replication_role",
        "dest_bucket",
        "dest_kms_key"
    ],
    "dest_sns_topic": [
        "dest_kms_key"
    ],
    "dest_ssm_param": [
        "dest_kms_key"
    ],
    "dest_lambda_function": [
        "dest_lambda_role",
        "dest_bucket"
    ],
    "dest_eventbridge_rule": [
        "dest_lambda_function",
        "dest_bucket"
    ],
    "src_kms_key": [
        "dest_copy_role"
    ],
    "src_bucket": [
        "dest_bucket",
        "dest_kms_key",
        "dest_copy_role"
    ]
}