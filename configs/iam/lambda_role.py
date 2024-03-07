LAMBDA_IAM_POLICY_TEMPLATE = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": "logs:CreateLogGroup",
            "Effect": "Allow",
            "Resource": "arn:aws:logs:*:$dest_account:*"
        },
        {
            "Action": [
                "logs:PutLogEvents",
                "logs:CreateLogStream"
            ],
            "Effect": "Allow",
            "Resource": "arn:aws:logs:*:$dest_account:log-group:/aws/lambda*"
        },
        {
            "Effect": "Allow",
            "Action": "s3:CreateJob",
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": "$dest_copy_role/arn"
        },
        {
            "Effect": "Allow",
            "Action": "kms:*", ## TODO fine tune this
            "Resource": "$dest_kms_key/#all/arn"
        },
        {
            "Effect": "Allow",
            "Action": "ssm:GetParameter",
            "Resource": "arn:aws:ssm:*:$dest_account:parameter/CloudCopyCat-*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": "$dest_bucket/#all/object_arn"
        }
    ]
}


LAMBDA_TRUST_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}