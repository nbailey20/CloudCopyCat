EVENT_PATTERN_TEMPLATE = {
    "source": ["aws.s3"],
    "detail-type": ["Object Created"],
    "detail": {
        "bucket": {
            "name": ["$dest_bucket/name"]
        },
        "object": {
            "key": [{
                "wildcard": "*/manifest.json"
            }]
        }
    }
}