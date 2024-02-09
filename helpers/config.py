SNS_TOPIC_NAME            = "CloudCopyCat-Notification-Topic"
KMS_ALIAS_NAME            = "alias/CloudCopyCat-KMS-Key"

LAMBDA_FUNCTION_NAME      = "CloudCopyCat-Lambda-Function"
LAMBDA_RUNTIME            = "python3.9"
LAMBDA_POLICY_NAME        = "CloudCopyCat-Lambda-IAM-Policy"
LAMBDA_ROLE_NAME          = "CloudCopyCat-Lambda-IAM-Role"
LAMBDA_STATE_FOLDER       = "CloudCopyCat-Data"
LAMBDA_STATE_FILE_NAME    = "CloudCopyCat-State"

REPLICATION_POLICY_NAME   = "CloudCopyCat-IAM-Replication-Policy"
REPLICATION_ROLE_NAME     = "CloudCopyCat-IAM-Replication-Role"

BATCH_COPY_POLICY_NAME    = "CloudCopyCat-IAM-Batch-Copy-Policy"
BATCH_COPY_ROLE_NAME      = "CloudCopyCat-IAM-Batch-Copy-Role"

EVENTBRIDGE_RULE_NAME     = "CloudCopyCat-EventBridge-Rule"
EVENTBRIDGE_RULE_TARGETID = "CloudCopyCat-EventBridge-Lambda-Target"