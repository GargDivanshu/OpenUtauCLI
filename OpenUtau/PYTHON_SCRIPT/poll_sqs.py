import json
import time
import logging

# Set up the logger
logger = logging.getLogger(__name__)

def poll_sqs(sqs_client, queue_url, process_message_fn, wait_time=20, max_messages=10, sleep_interval=5):
    """Poll the SQS queue and process messages.
    
    Args:
        sqs_client: The SQS client object.
        queue_url: The URL of the SQS queue.
        process_message_fn: The function to process each message.
        wait_time: Wait time for long-polling (default is 20 seconds).
        max_messages: The maximum number of messages to retrieve (default is 10).
        sleep_interval: The pause between each polling attempt (default is 5 seconds).
    """
    while True:
        response = sqs_client.receive_message(
            QueueUrl=queue_url,
            AttributeNames=['All'],
            MaxNumberOfMessages=max_messages,
            WaitTimeSeconds=wait_time
        )
        
        # Log the raw response for debugging
        logger.debug(f"Received response: {response}")
        messages = response.get("Messages", [])
        
        for message in messages:
            logger.debug(f"Processing message: {message}")
            try:
                # Parse the body of the message
                record_body = json.loads(message["Body"])
                logger.debug(f"Parsed record body: {record_body}")
                
                # Call the provided function to process the message
                process_message_fn(record_body)
                    
                # Delete the message after successful processing
                sqs_client.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=message["ReceiptHandle"]
                )
                logger.info(f"Message processed and deleted: {message['MessageId']}")
            
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")

        # Pause to avoid excessive polling
        time.sleep(sleep_interval)
