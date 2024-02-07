KMS_POLICY_TEMPLATE = {
    "Version": "2012-10-17",
    "Id": "key-default-1",
    "Statement": [
        {
            "Sid": "Enable IAM User Permissions",
            "Effect": "Allow",
            "Principal": {
                "AWS": "" ## to be filled in at deployment time
            },
            "Action": "kms:*",
            "Resource": "*"
        },
        {
            "Sid": "Allow Amazon S3 use of the KMS key",
            "Effect": "Allow",
            "Principal": {
                "Service": "s3.amazonaws.com"
            },
            "Action": [
                "kms:GenerateDataKey"
            ],
            "Resource": "*",
            "Condition":{
                "StringEquals":{
                    "aws:SourceAccount":"" ## to be filled in at deployment time
                },
                "ArnLike":{
                    "aws:SourceArn": [] ## to be filled in at deployment time
                }
            }
        }
        {
            "Sid": "Allow Batch role use of the KMS key",
            "Effect": "Allow",
            "Principal": {
                "AWS": "" ## to be filled in at deployment time
            },
            "Action": [
                "kms:GenerateDataKey",
                "kms:Decrypt",
                "kms:Encrypt"
            ],
            "Resource": "*"
        }
    ]
}
