REPLICATION_IAM_POLICY_TEMPLATE = {
	"Version": "2012-10-17",
	"Statement": [
		{
			"Action": [
				"s3:InitiateReplication",
				"s3:*"
			],
			"Effect": "Allow",
			"Resource": "$src_bucket/#all/object_arn"
		},
		{
			"Action": [
				"s3:GetReplicationConfiguration",
				"s3:PutInventoryConfiguration",
				"s3:*"
			],
			"Effect": "Allow",
			"Resource": "$src_bucket/#all/arn"
		},
		{
			"Action": [
				"s3:GetObject*",
				"s3:PutObject*",
				"s3:Replicate*",
				"s3:ObjectOwnerOverrideToBucketOwner",
				"s3:*"
			],
			"Effect": "Allow",
			"Resource": "$dest_bucket/#all/arn"
		},
        {
			"Action": [
				"s3:GetObject*",
				"s3:PutObject*",
				"s3:Replicate*",
				"s3:ObjectOwnerOverrideToBucketOwner",
				"s3:*"
			],
			"Effect": "Allow",
			"Resource": "$dest_bucket/#all/object_arn"
		},
		{
			"Action": [
				"kms:Encrypt",
                "kms:GenerateDataKey*"
			],
			"Effect": "Allow",
			"Resource": "$dest_kms_key/#all/arn"
		},
        {
			"Action": [
				"kms:Decrypt"
			],
			"Effect": "Allow",
			"Resource": "$src_kms_key/#all/arn"
		}
	]
}



REPLICATION_TRUST_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Principal": {
                "Service": [
                  "batchoperations.s3.amazonaws.com",
                  "s3.amazonaws.com"
                ]
            },
            "Action": "sts:AssumeRole"
        }
    ]
}