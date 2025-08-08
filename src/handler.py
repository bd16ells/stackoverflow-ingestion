from api.StackOverflow import StackOverflow
from util.aws import AWS
from datetime import datetime, timedelta
import os

from util.filter import Filter
from util.Parser.article_parser import ArticleParser


aws_client = AWS(region_name=os.environ.get("AWS_REGION", "us-east-1"))

def lambda_handler(event, context):
    """
    Basic AWS Lambda handler function.
    
    :param event: The event data passed to the Lambda function (dict)
    :param context: The runtime information of the Lambda function (object)
    :return: A response dict
    """
    # Log the received event
    print("Received event:", event)
    from_date = None
    if 'initial_load' not in event:
        if 'from_date' in event:
            from_date = event['from_date']
        else:
            now = datetime.now(datetime.timezone.utc)
            timestamp_24_hours_ago = now - timedelta(hours=24)
            # Convert to a UTC timestamp
            from_date = int(timestamp_24_hours_ago.timestamp())

    api_token = None
    ## allow local runs to use env var for API Key
    if os.environ.get("SSM_OVERRIDE", "false").lower() == "true":
        api_token = os.environ.get("STACKOVERFLOW_API_KEY")
    else:
        ssm_client = aws_client.get_ssm_client()
        try:
            response = ssm_client.get_parameter(Name=os.environ["STACKOVERFLOW_API_KEY_PARAM"], WithDecryption=True)
            api_token = response["Parameter"]["Value"]
        except Exception as e:
            print(f"Error retrieving SSM parameter: {e}")
            return {
                "statusCode": 500,
                "body": "Failed to retrieve API token from SSM."
            }
    stackoverflow_api = StackOverflow(
        api_url=os.environ["STACKOVERFLOW_API_URL"],
        api_token=api_token,
        from_date=from_date)
    
    ### START: Article retrieval and processing ################
    all_articles = stackoverflow_api.get_articles()
    print(f"Retrieved {len(all_articles)} articles from StackOverflow API.")
    article_filters = ["terraform", "tfe", "terraform-enterprise", "tfe-enterprise", "UDP", "gitlab", "gitlab-ci", "gitlab-ci-cd", "cicd", "venafi", "modules", "module", "gitlab-ci-pipelines", "gitlab-pipelines", "gitlab-pipeline", "devsecops", "devops"]
    article_filter = Filter(
        key="tags",
        values=article_filters,
        id_field="article_id"
    )
    article_ids = article_filter.do_filter(all_articles)
    print(f"Found {len(article_ids)} articles matching filters: {article_filters}")

    # parsing
    raw_output_dir = os.environ.get("RAW_OUTPUT_DIR", "/tmp")
    article_output_dir = f"{raw_output_dir}/articles"
    os.makedirs(article_output_dir, exist_ok=True)
    article_content_list = stackoverflow_api.get_articles_by_ids(article_ids=article_ids)
    for article in article_content_list:
        article_parser = ArticleParser(article)
        article_id = article.get("article_id", "unknown")
        outfile = os.path.join(article_output_dir, f"{article_id}.json")
        article_parser.parse_to_outfile(outfile)
        print(f"Parsed and saved article {article_id} to {outfile}")

    ### END: Article retrieval and processing ################
    ### START: Question retrieval and processing ################

    ### END: Question retrieval and processing ################

if __name__ == "__main__":
    # For local testing
    event = {
        "initial_load": True
    }
    lambda_handler(event, None)
