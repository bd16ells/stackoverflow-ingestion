import boto3

class AWS:
    def __init__(self, region_name="us-east-1"):
        """
        Initialize the AWS helper class.
        
        :param region_name: AWS region to use (default: us-east-1)
        """
        self.region_name = region_name

    def get_ssm_client(self):
        """
        Get a boto3 SSM client.
        
        :return: boto3 SSM client object
        """
        return boto3.client("ssm", region_name=self.region_name)