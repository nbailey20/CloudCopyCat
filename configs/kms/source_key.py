SOURCE_KMS_POLICY_TEMPLATE = {
    "Sid": "CloudCopyCat-BatchCopyDecrypt",
    "Effect": "Allow",
    "Principal": {
        "AWS": "$dest_copy_role/arn"
    },
    "Action": "kms:Decrypt",
    "Resource": "*"
}