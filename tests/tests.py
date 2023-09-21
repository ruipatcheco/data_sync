import unittest
from datetime import datetime
from unittest.mock import patch, Mock

from api.requestsModule import APIRequestError
from syncModule import (
    MAX_NUMBER_OF_CONCURRENT_RUNNING_THREADS,
    BULK_MEMBER_COUNT,
    sync_job_logic,
    launch_sync_job,
    launch_sync_jobs,
    wait_sync_jobs,
    open_jobs_dict,
    SyncJob,
    Status,
    JobDetails,
)

EXAMPLE_CORRECT_MEMBERS_LIST_FROM_MAILCHIMP = {'members': [{
    "id": "95d88d13bab1f2a4905915f9c99384b6",
    "email_address": "al.james+mc670@gmail.com",
    "status": "subscribed",
    "merge_fields": {
        "FNAME": "",
        "LNAME": "",
        "OM_STATUS": "LEAD",
        "OM_LTV": 0,
        "OM_ORDERS": 0,
        "OM_DATE_LO": "",
        "OM_DATE_LV": "",
        "DFALDFKJ": ""
    }
}, {
    "id": "3fb02ab7dda1e7d330c703650b844dcb",
    "email_address": "al.james+mc56@gmail.com",
    "status": "subscribed",
    "merge_fields": {
        "FNAME": "Niccole",
        "LNAME": "Beuoy",
        "OM_STATUS": "LEAD",
        "OM_LTV": 0,
        "OM_ORDERS": 0,
        "OM_DATE_LO": "",
        "OM_DATE_LV": "",
        "DFALDFKJ": ""
    }
}]}

EXAMPLE_CORRECT_MEMBER_COUNT = 2
EXAMPLE_LIST_ID = "1a2d7ebf82"
EXAMPLE_LIST_ID_2 = "829e85fee6"
EXAMPLE_DATETIME = "2023-09-14T10:00:00+00:00"
EXAMPLE_JOB_DETAILS = JobDetails(EXAMPLE_LIST_ID, EXAMPLE_DATETIME)


class TestSyncJob(unittest.TestCase):

    @patch('api.mailchimpAPIModule.get_list_members')
    @patch('api.mailchimpAPIModule.get_list_members_count')
    @patch('api.ometriaAPIModule.create_or_update_members')
    def test_sync_job_logic_success(self, mock_create_or_update_members, mock_get_list_members_count,
                                    mock_get_list_members):
        # Mock get_list_members_count to return a number of members
        mock_get_list_members_count.return_value = EXAMPLE_CORRECT_MEMBER_COUNT

        # Mock get_list_members to return a list of members
        mock_get_list_members.return_value = EXAMPLE_CORRECT_MEMBERS_LIST_FROM_MAILCHIMP

        job_details = EXAMPLE_JOB_DETAILS
        result = sync_job_logic(job_details)

        self.assertTrue(result)
        mock_create_or_update_members.assert_called()

    @patch('api.mailchimpAPIModule.get_list_members')
    @patch('api.mailchimpAPIModule.get_list_members_count')
    def test_sync_job_logic_failure(self, mock_get_list_members_count, mock_get_list_members):
        # Mock get_list_members_count to return 0 members
        mock_get_list_members_count.return_value = 0

        # Mock get_list_members to raise an APIRequestError
        mock_get_list_members.side_effect = APIRequestError("Test Error")

        job_details = EXAMPLE_JOB_DETAILS
        result = sync_job_logic(job_details)

        self.assertFalse(result)

    @patch('datetime.datetime')
    def test_launch_sync_job(self, mock_datetime):
        # Mock datetime.now to return a fixed date and time
        mock_datetime.now.return_value = datetime(2023, 9, 14, 12, 0, 0)

        job_details = EXAMPLE_JOB_DETAILS
        sync_job = SyncJob(job_details, Status.UNDEFINED)
        result = launch_sync_job(sync_job)

        self.assertEqual(result.status, Status.PARTIALLY_SYNCED)
        self.assertEqual(result.job_details.last_sync_date_time, "2023-09-14T12:00:00+00:00")

    def test_launch_sync_jobs(self):
        # Create a mock SyncJob object
        sync_job = Mock()
        sync_job.status = Status.UNDEFINED

        # Create a dictionary of test jobs
        test_jobs = {EXAMPLE_LIST_ID: sync_job}

        # Call launch_sync_jobs with the test jobs
        jobs, results = launch_sync_jobs(test_jobs)

        # Assert that the job status is updated
        self.assertEqual(jobs[EXAMPLE_LIST_ID].status, Status.RUNNING)

    def test_wait_sync_jobs(self):
        # Create a mock Future object
        mock_future = Mock()
        mock_future.result.return_value = SyncJob(JobDetails(EXAMPLE_LIST_ID, None), Status.PARTIALLY_SYNCED)

        # Create a dictionary of test results
        test_results = {EXAMPLE_LIST_ID: mock_future}

        # Create a mock SyncJob object
        sync_job = Mock()
        sync_job.status = Status.UNDEFINED

        # Create a dictionary of test jobs
        test_jobs = {EXAMPLE_LIST_ID: sync_job}

        # Call wait_sync_jobs with the test jobs and results
        jobs = wait_sync_jobs(test_jobs, test_results)

        # Assert that the job status is updated
        self.assertEqual(jobs[EXAMPLE_LIST_ID].status, Status.PARTIALLY_SYNCED)

    def test_initialize_jobs_dict(self):
        # Create a list of test list IDs
        test_id_lists = [EXAMPLE_LIST_ID, EXAMPLE_LIST_ID_2]

        # Call initialize_jobs_dict with the test list IDs
        jobs = open_jobs_dict(test_id_lists)

        # Assert that the jobs dictionary is created with the expected keys
        self.assertEqual(set(jobs.keys()), set(test_id_lists))


if __name__ == '__main__':
    unittest.main()
