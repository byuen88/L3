import os
import boto3
import logging
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

class BucketService:
    def __init__(self):
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
        s3_client = boto3.client('s3')
        try:
            s3_client.upload_file(file_name, self.bucket_name, object_name)
            print(f"Please wait a moment for the leaderboard to update.")
        except ClientError as e:
            logging.error(e)
            return False
        return True
