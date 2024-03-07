DEST_KMS_POLICY_TEMPLATE = {
    "Version": "2012-10-17",
    "Id": "key-default-1",
    "Statement": [
        {
            "Sid": "Enable IAM User Permissions",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::$dest_account:root"
            },
            "Action": "kms:*",
            "Resource": "*"
        },
        {
            "Sid": "Allow Amazon S3 use of the KMS key",
            "Effect": "Allow",
            "Principal": {
                "Service": [
                    "s3.amazonaws.com",
                    "batchoperations.s3.amazonaws.com"
                ]
            },
            "Action": [
                "kms:GenerateDataKey",
                "kms:*"
            ],
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "aws:SourceAccount": ["$src_account"] ## maybe needed "$dest_account"]
                },
                "ArnLike": {
                    "aws:SourceArn": [] ## filled in at deployment time"$src_bucket/#all/arn" ## maybe need destbucketarns
                }
            }
        },
        {
            "Sid": "Allow Replication role to deliver objects",
            "Effect": "Allow",
            "Principal": {
                "AWS": "*"
            },
            "Action": [
                "kms:Encrypt",
                "kms:GenerateDataKey*"
            ],
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "aws:PrincipalArn": "" ## to be filled in at deployment time to avoid cycle
                }
            }
        }
    ]
}
