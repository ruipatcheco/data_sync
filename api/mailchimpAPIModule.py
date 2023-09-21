import os

from logger.loggingModule import logger
from api.requestsModule import make_request

# Retrieve the Mailchimp API key from an environment variable
MAILCHIMP_API_KEY = os.getenv("MAILCHIMP_API_KEY")

# Check if the environment variable is set and handle the case if it's not
if MAILCHIMP_API_KEY is None:
    raise ValueError("MAILCHIMP_API_KEY environment variable is not set")

DEFAULT_BULK_MEMBER_COUNT = int(os.getenv("BULK_MEMBER_COUNT", "1000"))
DATA_CENTER = os.getenv("DATA_CENTER", "us9")
MAILCHIMP_BASE_URL = "https://{}.api.mailchimp.com/3.0/".format(DATA_CENTER)
MAILCHIMP_LIST_MEMBERS_URL = MAILCHIMP_BASE_URL + "lists/{}/members"
BASIC_AUTHENTICATION_HEADER = {
    'Authorization': "Basic {}".format(MAILCHIMP_API_KEY)
}


def get_list_members(list_id, page=1, count=DEFAULT_BULK_MEMBER_COUNT, since_last_changed=''):
    if page < 1:
        logger.log_error(f"Request pagination number must be positive: {page}")
        return
    url = MAILCHIMP_LIST_MEMBERS_URL.format(list_id)

    # Define the query parameters
    query_params = {
        # Unfortunatelly, members.merge_fields.[FNAME,LNAME]'s field filters do not work,
        # thus returning the entire members.merge_fields object...
        # the reason we're not using the full_name attribute is only due to the unsolvable
        # problem of splitting a full name onto first and last names.
        'fields': 'members.id,members.status,members.email_address,members.merge_fields.FNAME,'
                  'members.merge_fields.LNAME',
        'count': count,
        'offset': page * count,
        'since_last_changed': since_last_changed
    }

    return make_request('get', url, BASIC_AUTHENTICATION_HEADER, query_params)


def get_list_members_count(list_id, since_last_changed=None):
    url = MAILCHIMP_LIST_MEMBERS_URL.format(list_id)

    # Define the query parameters
    query_params = {
        'fields': 'total_items',
        'since_last_changed': since_last_changed
    }

    return make_request('get', url, BASIC_AUTHENTICATION_HEADER, query_params).get('total_items')
