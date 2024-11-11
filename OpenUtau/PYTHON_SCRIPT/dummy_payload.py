import json
import time

def get_dummy_payload():
    return {
            "Records": [
                {
                    "messageId": "unique-message-id",
                    "receiptHandle": "MessageReceiptHandle",
                    "body": json.dumps({"fileName": None, "songID": 108, "lyrics": "Jingle"}),
                    "attributes": {
                        "ApproximateReceiveCount": "1",
                        "SentTimestamp": str(int(time.time() * 1000)),
                        "SenderId": "108782080917",
                        "ApproximateFirstReceiveTimestamp": str(int(time.time() * 1000))
                    },
                    "messageAttributes": {},
                    "md5OfBody": "md5_of_body_placeholder",
                    "eventSource": "aws:sqs",
                    "eventSourceARN": "arn:aws:sqs:ap-south-1:108782080917:MyQueue",  # Replace with your SQS ARN if used
                    "awsRegion": "ap-south-1"
                }
            ]
        }