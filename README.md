# Ometria Challenge

## Introduction

The project aims to create a robust synchronization system for handling data synchronization between MailChimp and Ometria, facilitating efficient management of email marketing campaigns.

## Features

- **Asynchronous Data Sync**: Utilizes multithreading for concurrent synchronization, improving performance.
- **Dynamic Configuration**: Configurable parameters such as the maximum number of concurrent threads and bulk member count.
- **Error Handling**: Provides error handling for API requests, ensuring data integrity.
- **Persistence**: Stores job details in a JSON file for recovery and continuity.
- **Logging**: Implements a flexible logging system with configurable log levels and output destinations.
- **Automatic Sync**: Continuously monitors and syncs data, ensuring up-to-date records.

## Getting Started

### Prerequisites

Before you start, make sure you have the following prerequisites:

- Python 3.9+
- Pip
- Dependencies (see `requirements.txt`)

### Installation

1. Download and extract the tar.gz file

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Configuration:

   - Set environment variables (see Configuration section).

## Usage

To initiate data synchronization set the following environment variables:
`MAILCHIMP_API_KEY` and `OMETRIA_API_KEY`.

And then run the following command:

```bash
python syncModule.py list_id_1 list_id_2 ...
```

Replace `list_id_1`, `list_id_2`, etc., with the MailChimp list IDs you want to synchronize.

## Configuration

Configuration can be customized using environment variables:

- `MAX_NUMBER_OF_CONCURRENT_RUNNING_THREADS`: Maximum concurrent threads for synchronization (default: 2).
- `BULK_MEMBER_COUNT`: Number of members to process in each block (default: 5000).
- `MINUTES_NEEDED_TO_PERFORM_A_PARTIAL_SYNC_OF_A_SINGLE_BULK`: Time required for a partial sync (default: 1 minute).
- `NUMBER_OF_MINUTES_THAT_OMETRIAS_DATA_IS_BEHIND_MAILCHIMPS_DATA`: Time difference threshold (default: 120 minutes).
- `LOGGING_LEVEL`: Log level (default: DEBUG).
- `LOG_FILE`: Log file name (default: log_file.log).


## Docker Container

This project provides a Docker container for easy deployment and isolation. Follow these steps to build and run the container:

### Prerequisites

Before proceeding, ensure that you have Docker installed on your system. You can download and install Docker from [Docker's official website](https://docs.docker.com/get-docker/).

### Building the Docker Image

1. Download and extract the tar.gz file

2. Build the Docker image.

   ```bash
   docker build -t ometria-challenge .
   ```

   This command will use the provided Dockerfile to create an image with your project.

### Running the Docker Container

Once the Docker image is built, you can run the container:

```bash
docker run -t ometria-challenge python syncModule.py 1a2d7ebf82
```

This container also allows the mapping of the persistence file **sync_jobs.json** through the following command:

```bash
docker run -v path-to-folder-where-python-is-located/sync_jobs.json:/app/sync_jobs.json -t ometria-challenge python syncModule.py 1a2d7ebf82
```

or you can also redefine environment variables in the -e parameters, like so:

```bash
docker run -e MAX_NUMBER_OF_CONCURRENT_RUNNING_THREADS=2 -e BULK_MEMBER_COUNT=5000 -e ... your-image-name python syncModule.py list_id_1 list_id_2 ...
```

- You can set any necessary environment variables (e.g., `MAX_NUMBER_OF_CONCURRENT_RUNNING_THREADS`, `BULK_MEMBER_COUNT`, etc.) as needed for your specific configuration.
- Replace `list_id_1`, `list_id_2`, etc., with the MailChimp list IDs you want to synchronize.

### Stopping the Docker Container

To stop the running Docker container, you can use the following command:

```bash
docker stop container-id
```

Replace `container-id` with the actual ID of the running container, which you can find using `docker ps`.



## Acknowledgments

- Special thanks to the MailChimp and Ometria APIs for making data synchronization possible.
- The project was inspired by the need for efficient email marketing campaign management.


Certainly! Here's an updated README section regarding the Dockerfile and how to use it:
