import os
import boto3
import logging
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

class BucketService:
    def __init__(self):
        # TODO: remove aws_access_key_id, aws_secret_access_key, and aws_session_token when code is moved to EC2
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_session_token = os.getenv("AWS_SESSION_TOKEN")
        self.bucket_name = os.getenv("BUCKET_NAME")

    def upload_file(self, file_name, object_name=None):
        """Upload a file to an S3 bucket
        :param file_name: File to upload
        :param object_name: S3 object name. If not specified then file_name is used
        :return: True if file was uploaded, else False
        """
        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = os.path.basename(file_name)
        # Upload the file
        s3_client = boto3.client('s3', aws_access_key_id=self.aws_access_key_id, aws_secret_access_key=self.aws_secret_access_key, aws_session_token=self.aws_session_token)
        # TODO: replace above line with the line below when moved to EC2
        # s3_client = boto3.client('s3')
        try:
            s3_client.upload_file(file_name, self.bucket_name, object_name)
            print(f"Sucessfully uploaded file to S3 bucket, please wait a moment for the leaderboard to update.")
        except ClientError as e:
            logging.error(e)
            return False
        return True
