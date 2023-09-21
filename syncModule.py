import argparse
import json
import math
import os
import threading
import time
import concurrent.futures
from datetime import datetime, timedelta

from api.mailchimpAPIModule import get_list_members, get_list_members_count
from api.ometriaAPIModule import create_or_update_members
from api.requestsModule import APIRequestError
from classes.syncJob import SyncJob, Status, JobDetails
from logger.loggingModule import logger
from utils.utils import mailchimp_member_to_ometria_member, SyncJobEncoder

# Retrieve values from environment variables or use default values if not set
MAX_NUMBER_OF_CONCURRENT_RUNNING_THREADS = int(os.getenv("MAX_NUMBER_OF_CONCURRENT_RUNNING_THREADS", "2"))
BULK_MEMBER_COUNT = int(os.getenv("BULK_MEMBER_COUNT", "5000"))
MINUTES_NEEDED_TO_PERFORM_A_PARTIAL_SYNC_OF_A_SINGLE_BULK = int(
    os.getenv("MINUTES_NEEDED_TO_PERFORM_A_PARTIAL_SYNC_OF_A_SINGLE_BULK", "1"))

NUMBER_OF_MINUTES_THAT_OMETRIAS_DATA_IS_BEHIND_MAILCHIMPS_DATA = int(
    os.getenv("NUMBER_OF_MINUTES_THAT_OMETRIAS_DATA_IS_BEHIND_MAILCHIMPS_DATA", "120"))
POLLING_TIME_IN_SECONDS = int(os.getenv("POLLING_TIME_IN_SECONDS", "60"))

PERSISTENCE_JOBS_FILE_NAME = "sync_jobs.json"


def sync_job_logic(job_details: JobDetails):
    try:
        ometria_members_to_add = []

        # here, we're taking into account the since_last_changed detail of the job sync
        # when fetching the number of members to add to minimize data transfer
        number_of_members_to_add = get_list_members_count(job_details.list_id, since_last_changed= job_details.last_sync_date_time)

        # we want to process BULK_MEMBER_COUNT members per page/block
        number_of_member_pages_to_request = math.ceil(number_of_members_to_add / BULK_MEMBER_COUNT)

        sync_time_log_message = f"has been synced for the last time at {job_details.last_sync_date_time}"
        if not job_details.last_sync_date_time:
            sync_time_log_message = "has never been synced"
        logger.log_info(
            f"List {job_details.list_id} {sync_time_log_message} and from that time until now, {number_of_members_to_add} members were added/updated.")

        for request_page in range(1, number_of_member_pages_to_request + 1, 1):
            member_list = get_list_members(job_details.list_id, page=request_page, count=BULK_MEMBER_COUNT,
                                           since_last_changed=job_details.last_sync_date_time)
            # Hardcoded object keyword, not very pretty, I know :D there are better ways
            for mailchimp_member in member_list.get('members'):
                ometria_member = mailchimp_member_to_ometria_member(mailchimp_member)
                ometria_members_to_add.append(ometria_member)

            logger.log_info(f"Adding/updating {len(ometria_members_to_add)} members to ometria's database.")

            # Uploading the members to ometria endpoint
            create_or_update_members(ometria_members_to_add)
            ometria_members_to_add.clear()
        return True
    except APIRequestError as e:
        print(f"API request failed: {e}")
        return False


def launch_sync_job(sync_job: SyncJob):
    logger.log_info(
        f"Thread {threading.current_thread().getName()}: Starting sync on list {sync_job.job_details.list_id}.")

    old_sync_date_time = sync_job.job_details.last_sync_date_time
    # We want to keep track of the precise datetime when the sync job was started
    new_sync_date_time = datetime.now().isoformat()
    job_successful = sync_job_logic(sync_job.job_details)

    sync_job.job_details.last_sync_date_time = new_sync_date_time
    sync_job.status = Status.PARTIALLY_SYNCED if job_successful else Status.ERROR

    if not job_successful:
        # If the sync failed, we have to roll back to the last sync time
        sync_job.job_details.last_sync_date_time = old_sync_date_time

    return sync_job


def launch_sync_jobs(jobs):
    # Used to manage a pool of worker threads that can execute tasks concurrently.
    # max_workers specifies the maximum number of worker threads that can run concurrently
    # in the thread pool.
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_NUMBER_OF_CONCURRENT_RUNNING_THREADS)

    # Create a dictionary to store the results of the submitted jobs
    results = {}

    # Iterate through the lists and submit jobs to the thread pool
    for list_id, sync_job in jobs.items():
        sync_job = jobs.get(list_id)

        future = executor.submit(launch_sync_job, sync_job)
        results[list_id] = future  # Store the Future object

        # Update the jobs execution status
        sync_job.status = Status.RUNNING
        jobs[list_id] = sync_job

    return jobs, results


def wait_sync_jobs(jobs, results):
    # Wait for all threads to complete
    concurrent.futures.wait(results.values())

    # Obtain the results of completed tasks
    for list_id, future in results.items():
        try:
            # Get the result of the task
            sync_job = future.result()
            sync_job.status = Status.PARTIALLY_SYNCED
            # Update the object
            jobs[list_id] = sync_job

            print(f"Result for list_id {list_id}: {sync_job.to_dict()}")
        except Exception as e:
            # Get the result of the task
            sync_job = jobs[list_id]
            sync_job.status = Status.ERROR
            # Update the object
            jobs[list_id] = sync_job

            print(f"Error for list_id {list_id}: {e}")
    return jobs


def open_jobs_dict(id_lists, filename):
    jobs = {}
    try:
        with open(filename, 'r') as file:
            jobs_json = json.load(file)
            for list_id, job_json in jobs_json.items():
                job_details = JobDetails(list_id, job_json.get('job_details').get('last_sync_date_time'))
                # Fill out the jobs dictionary with the newly parsed job
                jobs[list_id] = SyncJob(job_details=job_details, status=Status(job_json.get('status')))
            if len(jobs) < 0:
                logger.log_error(f"Failed to read jobs from persistence file {filename}")
            else:
                logger.log_info(f"Successfully read jobs from persistence file {filename}")
    except (FileNotFoundError, json.JSONDecodeError):
        logger.log_error(f"Error reading jobs from persistence file {filename}")

    # In the case where we've received a new list_id to keep track of that was not persisted,
    # we shall add it to the jobs dictionary as well so that it can be synced
    for list_id in id_lists:
        if list_id not in jobs:
            job_details = JobDetails(list_id, None)
            jobs[list_id] = SyncJob(job_details, Status.UNDEFINED)

    return jobs


def save_jobs_dict(jobs, filename):
    logger.log_info(f"Persisting sync jobs to file {filename}")
    # Save the updated jobs to the file
    with open(filename, 'w') as file:
        json.dump(jobs, file, indent=4, cls=SyncJobEncoder)


def is_sync_needed(job: SyncJob):
    last_sync_date_time = job.job_details.last_sync_date_time
    sync_needed_due_to_never_having_been_synced = last_sync_date_time is None

    # This is the scenario where a list is being populated
    if sync_needed_due_to_never_having_been_synced:
        return True

    # This is the scenario where we retry to sync due to an error that we might be able
    # to overcome via retry
    sync_needed_due_to_failed_sync = job.status == Status.ERROR
    if sync_needed_due_to_failed_sync:
        return True

    number_of_members_to_add = get_list_members_count(job.job_details.list_id, last_sync_date_time)
    sync_needed_due_to_member_changes = number_of_members_to_add > BULK_MEMBER_COUNT

    # This is the partial sync scenario, that is, the list has already been populated at a time X,
    # and we're now syncing partials (members that have been added/updated after X)
    if sync_needed_due_to_member_changes:
        return True

    last_sync_time_difference_from_now_in_seconds = datetime.now() - datetime.fromisoformat(last_sync_date_time)
    max_allowed_time_difference_before_sync_in_seconds = timedelta(seconds=(
                                                                                   NUMBER_OF_MINUTES_THAT_OMETRIAS_DATA_IS_BEHIND_MAILCHIMPS_DATA - MINUTES_NEEDED_TO_PERFORM_A_PARTIAL_SYNC_OF_A_SINGLE_BULK) * 60)

    sync_needed_due_to_time_restrictions = last_sync_time_difference_from_now_in_seconds > max_allowed_time_difference_before_sync_in_seconds

    # This is the scenario where we're triggering a sync if the number of members that require
    # syncing (added/updated since time the last sync) has become greater than our desired bulk
    # size... or due to the last sync time being almost 2h old
    return sync_needed_due_to_time_restrictions


def main(id_lists):
    # Obtain the jobs from the persistence file
    jobs = open_jobs_dict(id_lists, PERSISTENCE_JOBS_FILE_NAME)
    jobs_that_need_sync = {}

    while 1:
        for (list_id, job) in jobs.items():
            if is_sync_needed(job):
                # We've found a job that needs to be synced
                jobs_that_need_sync[list_id] = job
        if len(jobs_that_need_sync) > 0:
            (jobs_that_need_sync, results) = launch_sync_jobs(jobs_that_need_sync)
            jobs_that_need_sync = wait_sync_jobs(jobs_that_need_sync, results)

            # Update the jobs dict with the newly synced jobs
            for (newly_synced_list_id, newly_synced_job) in jobs_that_need_sync.items():
                jobs[newly_synced_list_id] = newly_synced_job

            # Clear the help dict of all the newly synced jobs
            jobs_that_need_sync.clear()

            # Persist the new information
            save_jobs_dict(jobs, PERSISTENCE_JOBS_FILE_NAME)
        else:
            logger.log_info("Nothing to do, sleeping...")
        time.sleep(POLLING_TIME_IN_SECONDS)


if __name__ == "__main__":
    # Create an ArgumentParser object with a description (useful for error messages)
    parser = argparse.ArgumentParser(description="Sync job lists.")

    # Define a positional argument named "id_lists" that accepts one or more values
    # Usage example: python syncModule.py 1a2d7ebf82 1a2d7ebf83 another_list_id...
    parser.add_argument("id_lists", nargs="+", help="List of id_lists to process")

    # Parse the command-line arguments using the ArgumentParser
    args = parser.parse_args()

    # Call the main function with the parsed "id_lists" argument as input
    main(args.id_lists)

