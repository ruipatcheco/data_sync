import json

from classes.ometriaMember import OmetriaMember
from urllib.parse import quote

from classes.syncJob import SyncJob


def custom_urlencode(query_params):
    # Iterate through the query parameters and encode each one
    encoded_params = []
    for key, value in query_params.items():
        if isinstance(value, str):
            # If the value is a string, encode it using quote
            encoded_value = quote(value, safe=',')  # Allow commas to remain unencoded
        else:
            encoded_value = str(value)
        encoded_params.append(f"{key}={encoded_value}")

    # Join the encoded parameters with "&" to create the final query string
    return "&".join(encoded_params)


def mailchimp_member_to_ometria_member(mailchimpMember):
    # Sample data: members.id,members.status,members.email_address,members.merge_fields.FNAME,members.merge_fields.LNAME

    subscriber_data = {
        "id": mailchimpMember.get('id'),
        "firstname": mailchimpMember.get('merge_fields').get('FNAME'),
        "lastname": mailchimpMember.get('merge_fields').get('LNAME'),
        "email": mailchimpMember.get('email_address'),
        "status": mailchimpMember.get('status')
    }

    # Create an instance of the Subscriber class using the sample data
    ometria_member = OmetriaMember(
        **subscriber_data)  # unpacks the contents of the subscriber_data dictionary and passes them as named arguments, very nice!

    return ometria_member


class SyncJobEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, SyncJob):
            # Convert a SyncJob object to a dictionary that can be serialized
            return {
                "job_details": obj.job_details.__dict__,
                "status": obj.status.value,
                "user readable status": obj.status.name,
            }
        return super().default(obj)