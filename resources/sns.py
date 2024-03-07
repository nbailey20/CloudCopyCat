from classes.ApiCall import ApiCall
from classes.Resource import Resource
from helpers.config import SNS_TOPIC_NAME


def dest_sns_topic(email_address):
    ## Creation API
    create_topic = ApiCall(
        method = "create_topic",
        method_args = {
            "KmsMasterKeyId": "$dest_kms_key/arn"
        },
        output_keys = {"arn": "TopicArn"}
    )
    subscribe_target = ApiCall(
        method = "subscribe",
        method_args = {
            "TopicArn": "$dest_sns_topic/arn",
            "Protocol": "email",
            "Endpoint": email_address
        }
    )

    ## Describe API
    describe_topic = ApiCall(
        method = "list_topics",
        output_keys = {"arn": f"Topics/?/TopicArn~{SNS_TOPIC_NAME}/TopicArn"}
    )

    ## Delete API
    delete_topic = ApiCall(
        method = "delete_topic",
        method_args = {"TopicArn": "$dest_sns_topic/arn"}
    )

    topic_resource = Resource(
        name = "dest_sns_topic",
        type = "sns",
        create_apis = (create_topic, subscribe_target),
        describe_apis = (describe_topic,),
        delete_apis = (delete_topic,)
    )
    return topic_resource