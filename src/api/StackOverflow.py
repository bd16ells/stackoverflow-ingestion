import requests

class StackOverflow:
    def __init__(self, api_url, api_token, from_date=None, cert_path=None):
        """
        Initialize the StackOverflow API client.
        
        :param api_url: Base URL for the StackOverflow API
        :param api_token: API token for authentication
        """
        self.api_url = api_url
        self.api_token = api_token
        # self.headers = {"Authorization": f"Bearer {self.api_token}"}
        self.articles_with_body_filter = "!nNPvSNW(gA" # from sample API requests
        self.from_date_filter = f"fromdate={from_date}" if from_date else None
        self.questions_with_answers_and_body_filter = "!6WPIomnMNcVD9" # from sample api requests
        self.cert_path = cert_path

    def build_query_params(self, params):
        """
        Build a dictionary of query parameters.
        
        :param params: Any number of key-value pairs as query parameters
        :return: A dictionary of query parameters
        """
        query_params = {"key": self.api_token}
        # Automatically add the date filter if provided
        if self.from_date_filter:
            query_params["fromdate"] = self.from_date_filter.split("=")[1]

        # Add other parameters
        if params is not None:
            query_params.update(params)

        return query_params

    def _make_request(self, endpoint, params=None):
        """
        Helper method to make a GET request to the API.
        
        :param endpoint: API endpoint to call
        :param params: Query parameters for the request
        :return: JSON response from the API
        """
        url = f"{self.api_url}/{endpoint}"
        query_params = None
        if params is None:
            params = {}
        # if add_body_filter:
        #     params.update({"filter": self.articles_with_body_filter})
        #     query_params = self.build_query_params(params)
        else:
            query_params = self.build_query_params(params)
        response = requests.get(url, params=query_params, verify=self.cert_path, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_questions(self, page_size=100):
        """
        Get all questions from the API, handling pagination.
        
        :param page_size: Number of items per page
        :return: List of questions
        """
        questions = []
        page = 0
        has_more = True

        while has_more:  # limit to first 10 pages for testing
            params = {"pagesize": page_size}
            if page > 0:
                params["page"] = page
            params["filter"] = self.articles_with_body_filter
            data = self._make_request("questions", params)
            questions.extend(data.get("items", []))
            has_more = data.get("has_more", False)
            page += 1

        return questions
    
    def get_questions_answers(self, question_ids, page_size=100):
        """
        Get all questions from the API, handling pagination.
        
        :param page_size: Number of items per page
        :return: List of questions
        """
        answers = []
        batch_size = 25

        for i in range(0, len(question_ids), batch_size):
            batch = question_ids[i:i + batch_size]
            ids_param = ";".join(map(str, batch))
            ## uses a diff filter for body
            data = self._make_request(f"questions/{ids_param}/answers", params={'filter': 'withbody'})
            answers.extend(data.get("items", []))
        return answers

    def get_articles(self, page_size=100):
        """
        Get all articles from the API, handling pagination.
        
        :param page_size: Number of items per page
        :return: List of articles
        """
        articles = []
        page = 0
        has_more = True

        while has_more:
            params = {"pagesize": page_size}
            if page > 0:
                params["page"] = page
            params["filter"] = self.articles_with_body_filter
            data = self._make_request("articles", params)
            articles.extend(data.get("items", []))
            has_more = data.get("has_more", False)
            page += 1

        return articles

    def get_questions_by_ids(self, question_ids):
        """
        Get questions by their IDs, batching requests in sizes of 25.
        
        :param question_ids: List of question IDs
        :return: List of question details
        """
        questions = []
        batch_size = 25

        for i in range(0, len(question_ids), batch_size):
            batch = question_ids[i:i + batch_size]
            ids_param = ";".join(map(str, batch))
            params = {"filter": self.questions_with_answers_and_body_filter}
            data = self._make_request(f"questions/{ids_param}", params=params)
            questions.extend(data.get("items", []))
        return questions

    def get_articles_by_ids(self, article_ids):
        """
        Get articles by their IDs, batching requests in sizes of 25.
        
        :param article_ids: List of article IDs
        :return: List of article details
        """
        articles = []
        batch_size = 25

        for i in range(0, len(article_ids), batch_size):
            batch = article_ids[i:i + batch_size]
            ids_param = ";".join(map(str, batch))
            data = self._make_request(f"articles/{ids_param}", params={"filter": self.articles_with_body_filter})
            articles.extend(data.get("items", []))

        return articles