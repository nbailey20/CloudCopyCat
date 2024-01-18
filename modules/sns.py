from helpers.config import SNS_TOPIC_NAME


def create_sns_topic(session, kms_id, target_email):
    client = session.client("sns")

    topic_arn = client.create_topic(
        Name = SNS_TOPIC_NAME,
        Attributes = {
           # Policy =
           "KmsMasterKeyId": kms_id
        }
    )["TopicArn"]
    
    client.subscribe(
        TopicArn = topic_arn,
        Protocol = "email",
        Endpoint = target_email
    )
    return



def delete_sns_topic(session):
    client = session.client("sns")
    all_topics = client.list_topics()["Topics"]

    topic_arn = [t["TopicArn"] for t in all_topics
                    if SNS_TOPIC_NAME in t["TopicArn"]]
    if not topic_arn:
        return
    topic_arn = topic_arn[0]

    client.delete_topic(
        TopicArn = topic_arn
    )
    return