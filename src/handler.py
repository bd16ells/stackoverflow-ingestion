from api.StackOverflow import StackOverflow
from api.confluence import ConfluenceAPI
from util.Parser.question_parser import QuestionParser
from util.aws import AWS
from datetime import datetime, timedelta
import os
import json
import sys
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
        from_date=from_date,
        cert_path=os.environ.get("CERT_PATH", None)
    )
    
    ### START: Article retrieval and processing ################
    print("Fetching articles from StackOverflow API...")
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
    print("Fetching questions from StackOverflow API...")
    all_questions = stackoverflow_api.get_questions()
    print(f"Retrieved {len(all_questions)} questions from StackOverflow API.")
    question_filters = ["terraform", "tfe", "terraform-enterprise", "tfe-enterprise", "UDP", "gitlab", "gitlab-ci", "gitlab-ci-cd", "cicd", "venafi", "modules", "module", "gitlab-ci-pipelines", "gitlab-pipelines", "gitlab-pipeline", "devsecops", "devops"]
    question_filter = Filter(
        key="tags",
        values=question_filters,
        id_field="question_id"
    )
    question_ids = question_filter.do_filter(all_questions)
    print(f"Found {len(question_ids)} questions matching filters: {question_filters}")

    # parsing
    raw_output_dir = os.environ.get("RAW_OUTPUT_DIR", "/tmp")
    question_output_dir = f"{raw_output_dir}/questions"
    os.makedirs(question_output_dir, exist_ok=True)
    question_content_list = stackoverflow_api.get_questions_by_ids(question_ids=question_ids)
    for question in question_content_list:
        question_parser = QuestionParser(question)
        question_id = question.get("question_id", "unknown")
        outfile = os.path.join(question_output_dir, f"{question_id}.json")
        question_parser.parse_to_outfile(outfile)
        print(f"Parsed and saved question {question_id} to {outfile}")

    # ### END: Question retrieval and processing ################
    ### START: Confluence processing ################
    print("Fetching Confluence pages...")
    ## allow local runs to use env var for API Key
    if os.environ.get("SSM_OVERRIDE", "false").lower() == "true":
        api_token = os.environ.get("CONFLUENCE_API_KEY")
    else:
        ssm_client = aws_client.get_ssm_client()
        try:
            response = ssm_client.get_parameter(Name=os.environ["CONFLUENCE_API_KEY_PARAM"], WithDecryption=True)
            api_token = response["Parameter"]["Value"]
        except Exception as e:
            print(f"Error retrieving SSM parameter: {e}")
            return {
                "statusCode": 500,
                "body": "Failed to retrieve API token from SSM."
            }
    # 1. https://confluence:8443/spaces/SSSECIWS01/pages/892986628/TFE+AWS
    # 2. https://confluence:8443/spaces/UP/pages/1521043813/Gitlab+Customer+Documentation
    # 3. https://confluence:8443/spaces/UP/pages/1235260306/UDP+2024-Production+Releases
    # 4. https://confluence:8443/spaces/UP/pages/1524995199/UDP+2025-Production+Releases
    # 5. https://confluence:8443/spaces/ENDO/pages/605591958/Operational+Workflows+-+AWS+Scripts+Usage+and+Jenkins+Setup
    # 6. https://confluence:8443/spaces/ENDO/pages/1503249254/GitLab+Operational+Workflow+Template+Mapping
    # starting_pages = [tuple(pair) for pair in json.loads(os.environ.get("CONFLUENCE_PAGES_TUPLE", "[]"))]
    starting_pages = [  ("892986628", "tfe"), ("1521043813", "gitlab"), ("1235260306", "gitlab"), ("1524995199", "gitlab"), ("605591958", "ops-tasks")]
    raw_output_dir = os.environ.get("RAW_OUTPUT_DIR", "/tmp")
    confluence_output_dir = f"{raw_output_dir}/confluence"
    confluence_api = ConfluenceAPI(
        api_url=os.environ["CONFLUENCE_API_URL"],
        api_token=api_token,
        cert_path=os.environ.get("CERT_PATH", None),
        output_dir=os.environ.get("CONFLUENCE_OUTPUT_DIR", confluence_output_dir)
    )

    ## straying a bit from the stackoverflow pattern here, as confluence requires some recursion and it's simplest
    ## to allow the confluenceAPI to handle the parsing itself. TODO: refactor maybe?
    for page, classifier in starting_pages:
        confluence_api.do_process(page, classifier)

    ## custom execution for one-off gitlab YBYO page
    # ("1503249254", "gitlab-ops-tasks")
    confluence_api.process_single_page("1503249254", "gitlab-ops-tasks")
    ### END: Confluence processing ################

if __name__ == "__main__":
    # For local testing
    event = {
        "initial_load": True
    }
    lambda_handler(event, None)
