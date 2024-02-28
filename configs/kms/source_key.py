SOURCE_KMS_POLICY_TEMPLATE = {
    "Sid": "CloudCopyCat-BatchCopyDecrypt",
    "Effect": "Allow",
    "Principal": {
        "AWS": "" ## to be filled in at deployment time
    },
    "Action": "kms:Decrypt",
    "Resource": "*"
}