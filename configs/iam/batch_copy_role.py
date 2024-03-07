BATCH_COPY_IAM_POLICY_TEMPLATE = {
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowBatchOperationObjectGet",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:GetObjectAcl",
        "s3:GetObjectTagging",
        "s3:GetObjectVersionAcl",
        "s3:GetObjectVersionTagging"
      ],
      "Resource": "$src_bucket/#all/object_arn"
    },
    {
      "Sid": "AllowBatchOperationDestinationObjectPut",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectVersionAcl",
        "s3:PutObjectAcl",
        "s3:PutObjectVersionTagging",
        "s3:PutObjectTagging",
        "s3:GetObject",
        "s3:GetObjectVersion"
      ],
      "Resource": "$dest_bucket/#all/object_arn"
    },
    {
      "Sid": "AllowDestKMSUsage",
      "Effect": "Allow",
      "Action": [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:GenerateDataKey*"
        ],
      "Resource": "$dest_kms_key/#all/arn"
    },
    {
      "Sid": "AllowSourceKMSUsage",
      "Effect": "Allow",
      "Action": [
          "kms:Decrypt"
        ],
      "Resource": "$src_kms_key/#all/arn"
    }
  ]
}



BATCH_COPY_TRUST_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Principal": {
                "Service": "batchoperations.s3.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}