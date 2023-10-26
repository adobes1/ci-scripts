#!/usr/bin/env python3

# This script updates Quay image description

import os
import sys
import requests
from typing import Optional, List

Response = requests.models.Response # Type alias for type-checking


def print_api_error(response: Response) -> None:
    errors = {
        400: "Bad Request",
        401: "Session required",
        403: "Unauthorized access",
        404: "Not found"
    }
    
    detail_key = "detail" # Key which corresponds to better error description
    if "error" in response.json().keys():
        detail_key = "error"
    print(f"{errors[response.status_code]}: {response.json()[detail_key]}")


def load_readme_as_list(dir: str) -> Optional[List[str]]:
    readme_path = os.path.join(dir, "README.md")
    print(f"Reading README from {readme_path}")
    if not os.path.isfile(readme_path):
        print(f"Invalid path: {readme_path} does not exist")
        return None
    with open(readme_path) as readme:
        lines = readme.readlines()
        # for i, line in enumerate(lines):
        #     if re.match("Description", line):
        #         if i + 3 >= len(lines):
        #             break
        #         print(f"{readme_path} successfully loaded")
        #         return lines[i + 3:]
        return lines
    # print("Invalid README format")
    # return None


def escape_code_block(lines: List[str]) -> None:
    """
    Ensures that all markdown code blocks created by backticks (```) were correctly
    closed, so that any lines added afterwards will be outside of a code block.
    Unclosed code blocks can occur after shortening readme.
    """
    backtick_count = 0
    for line in lines:
        if "```" in line:
            backtick_count += 1
    if backtick_count % 2 == 1:
        lines.append("...\n```")


def shorten_readme(readme_as_list: List[str]) -> List[str]:
    """
    Shorten readme if it is too long
    """
    readme_as_list = readme_as_list[:98]
    escape_code_block(readme_as_list) 
    readme_as_list.append("\n<br>\n")
    readme_as_list.append(f"Learn more at <https://github.com/sclorg/{github_repo}/blob//master/{context}/README.md>")
    return readme_as_list



def update_description(readme: str) -> bool:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "description": readme
    }
    
    print(f"Sending request to {API_REQUEST_PATH}")
    response = requests.put(API_REQUEST_PATH, headers=headers, json=data)
    if response.status_code != 200:
        print_api_error(response)
        return False
    return True


if __name__ == "__main__":
    token = os.environ["QUAY_IMAGE_UPDATE_DESC"] # Quay application token
    image_name = os.environ["IMAGE_NAME"] # Quay image name
    registry_namespace = os.environ["REGISTRY_NAMESPACE"] # Quay namespace
    context = os.environ["DOCKER_CONTEXT"] # Build Context
    github_repo = os.environ["GITHUB_REPO"] # Name of repo on github

    API_REQUEST_PATH = f"https://quay.io/api/v1/repository/{registry_namespace}/{image_name}"
    
    readme_as_list = load_readme_as_list(context)
    if readme_as_list is None:
        sys.exit(1)
    if len(readme_as_list) > 100:
        readme_as_list = shorten_readme(readme_as_list)
    
    readme = "".join(readme_as_list)
    if not update_description(readme):
        sys.exit(1)
    print("Operation successful: description updated")
