import json
import logging
import os
from typing import List

import yaml
from qdrant_client import QdrantClient

from scripts.utils.logger import init_logging_config

init_logging_config(basic_log_level=logging.INFO)
# Get the logger
logger = logging.getLogger(__name__)

# Set the logging level
logger.setLevel(logging.INFO)


def find_path(folder_name):
    """
    Find the path of a folder with the given name in the current directory or its parent directories.

    Args:
        folder_name (str): The name of the folder to search for.

    Returns:
        str: The path of the folder if found.

    Raises:
        ValueError: If the folder with the given name is not found in the current directory or its parent directories.
    """
    # In Docker, we're already in the app directory
    curr_dir = os.getcwd()
    if folder_name in os.listdir(curr_dir):
        return os.path.join(curr_dir, folder_name)
    # If not found, return the current directory since we're already in the app directory
    return curr_dir


cwd = find_path("Resume-Matcher")
READ_RESUME_FROM = os.path.join(cwd, "Data", "Processed", "Resumes")
READ_JOB_DESCRIPTION_FROM = os.path.join(cwd, "Data", "Processed", "JobDescription")
config_path = os.path.join(cwd, "scripts", "similarity")

# Ensure directories exist
os.makedirs(READ_RESUME_FROM, exist_ok=True)
os.makedirs(READ_JOB_DESCRIPTION_FROM, exist_ok=True)
os.makedirs(config_path, exist_ok=True)


def read_config(filepath):
    """
    The `read_config` function reads a configuration file in YAML format and handles exceptions related
    to file not found or parsing errors.

    Args:
      filepath: The `filepath` parameter in the `read_config` function is a string that represents the
    path to the configuration file that you want to read and parse. This function attempts to open the
    file specified by `filepath`, load its contents as YAML, and return the parsed configuration. If any
    errors occur during

    Returns:
      The function `read_config` will return the configuration loaded from the file if successful, or
    `None` if there was an error during the process.
    """
    try:
        with open(filepath) as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError as e:
        logger.error(f"Configuration file {filepath} not found: {e}")
    except yaml.YAMLError as e:
        logger.error(
            f"Error parsing YAML in configuration file {filepath}: {e}", exc_info=True
        )
    except Exception as e:
        logger.error(f"Error reading configuration file {filepath}: {e}")
    return None


def read_doc(path):
    """
    The `read_doc` function reads a JSON file from the specified path and returns its contents, handling
    any exceptions that may occur during the process.

    Args:
      path: The `path` parameter in the `read_doc` function is a string that represents the file path to
    the JSON document that you want to read and load. This function reads the JSON data from the file
    located at the specified path.

    Returns:
      The function `read_doc(path)` reads a JSON file located at the specified `path`, and returns the
    data loaded from the file. If there is an error reading the JSON file, it logs the error message and
    returns an empty dictionary `{}`.
    """
    with open(path) as f:
        try:
            data = json.load(f)
        except Exception as e:
            logger.error(f"Error reading JSON file: {e}")
            data = {}
    return data


def get_score(resume_string, job_description_string):
    """
    The function `get_score` uses QdrantClient to calculate the similarity score between a resume and a
    job description.

    Args:
      resume_string: The `resume_string` parameter is a string containing the text of a resume. It
    represents the content of a resume that you want to compare with a job description.
      job_description_string: The `get_score` function you provided seems to be using a QdrantClient to
    calculate the similarity score between a resume and a job description. The function takes in two
    parameters: `resume_string` and `job_description_string`, where `resume_string` is the text content
    of the resume and

    Returns:
      The function `get_score` returns the search result obtained by querying a QdrantClient with the
    job description string against the resume string provided.
    """
    logger.info("Started getting similarity score")

    documents: List[str] = [resume_string]
    client = QdrantClient(":memory:")
    client.set_model("BAAI/bge-base-en")

    client.add(
        collection_name="demo_collection",
        documents=documents,
    )

    search_result = client.query(
        collection_name="demo_collection", query_text=job_description_string
    )
    logger.info("Finished getting similarity score")
    return search_result


if __name__ == "__main__":
    # To give your custom resume use this code
    resume_dict = read_config(
        READ_RESUME_FROM
        + "/Resume-alfred_pennyworth_pm.pdf83632b66-5cce-4322-a3c6-895ff7e3dd96.json"
    )
    job_dict = read_config(
        READ_JOB_DESCRIPTION_FROM
        + "/JobDescription-job_desc_product_manager.pdf6763dc68-12ff-4b32-b652-ccee195de071.json"
    )
    resume_keywords = resume_dict["extracted_keywords"]
    job_description_keywords = job_dict["extracted_keywords"]

    resume_string = " ".join(resume_keywords)
    jd_string = " ".join(job_description_keywords)
    final_result = get_score(resume_string, jd_string)
    for r in final_result:
        print(r.score)
