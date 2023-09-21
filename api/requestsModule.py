import requests
import json

from logger.loggingModule import logger


class APIRequestError(Exception):
    pass


def make_request(request_type, url, headers, query_params=None, data=None, json_data=None):
    try:
        request_type = request_type.lower()
        request_functions = {
            'get': requests.get,
            'post': requests.post,
            'put': requests.put,
            'delete': requests.delete
        }

        if request_type not in request_functions:
            raise ValueError(f"Unsupported request type: {request_type}")

        request_function = request_functions[request_type]

        response = request_function(url, headers=headers, params=query_params, data=data, json=json_data)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)

        # Log information about the successful request
        # logger.log_info(f"Request to {url} was successful.")

        # Parse the JSON response
        return json.loads(response.text)

    except requests.exceptions.RequestException as e:
        # Log the error and raise APIRequestError
        error_message = f"Request to {url} failed with exception: {e}"
        logger.log_error(error_message)
        raise APIRequestError(error_message)
