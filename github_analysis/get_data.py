"""
.. module:: github_analysis.get_data
.. moduleauthor:: Luka Lodrant <luka.lodrant@gmail.com

Python script which downloads the current data from Github and stores it into data.csv

"""

import requests
import re
import json
import csv
from urllib.parse import urlencode

GITHUB_MOST_STARRED_URL="https://github.com/search?o=desc&p={}&q=stars%3A%3E1&s=stars&type=Repositories"
GITHUB_SITE_URL = "https://github.com/"
GITHUB_API_URL = "https://api.github.com/repos/"
GITHUB_SEARCH_API_URL = "https://api.github.com/search/repositories"
CSV_FILENAME = "../data/repositories.csv"


def get_repository_regex(full_name):
    """
    Downloads HTML repositories page from Github and parses what is unavailable in the JSON API.

    :param full_name: Full name of the Github repository (eg. lodrantl/github_analysis)
    :return: Dict with the info about the repository

    """

    site = requests.get(GITHUB_SITE_URL + full_name).text

    # get commit, branch, release, and contributor
    regex_cbrcl = re.compile(r'<li class="commits">.*?<span class="num text-emphasized">.*?(\d+).*?</span>'
                             r'.*?<span class="num text-emphasized">.*?(\d+).*?</span>'
                             r'.*?<span class="num text-emphasized">.*?(\d+).*?</span>'
                             r'.*?<span class="num text-emphasized">.*?(\d+).*?</span>', re.DOTALL | re.MULTILINE)
    cbrc = regex_cbrcl.findall(site)[0]

    return {
        "commit_count": int(cbrc[0]),
        "branch_count": int(cbrc[1]),
        "release_count": int(cbrc[3]),
        "contributor_count": int(cbrc[2])
    }


def get_repository_licence(full_name):
    """
    Downloads repository licence name if available

    :param full_name: Full name of the Github repository (eg. lodrantl/github_analysis)
    :return: Licence name
    """

    license_json_data = requests.get(GITHUB_API_URL + full_name + "/license").text

    license_data = json.loads(license_json_data)

    if "license" in license_data and "name" in license_data["license"]:
        return license_data["license"]["name"]
    else:
        return "None"


def fill_repository(data):
    """
    Downloads JSON repositories info from Github API and parses the available data

    :param data: JSON data recieved from search
    :return: Dict with the info about the repository

    """

    result = {
        "name": data["name"],
        "owner": data["owner"]["login"],
        "watchers_count": data["watchers_count"],
        "stargazers_count": data["stargazers_count"],
        "forks_count": data["forks_count"],
        "open_issues_count": data["open_issues_count"],
        "language": data["language"],
        "created_at": data["created_at"],
        "updated_at": data["updated_at"],
        "pushed_at": data["pushed_at"]
    }

    license_name = get_repository_licence(data["full_name"])
    result["license"] = license_name

    return {**result, **get_repository_regex(data["full_name"])}


def repository_generator(n):
    """
    Yields a generator of first 1000 most starred repositories.

    :param n: number of pages (100 per page)
    :return: list of full names
    """


    request_data = {
        "q": "stars:>1",
        "sort": "stars",
        "order": "desc",
        "type": "Repositories",
        "per_page": 100
    }

    for i in range(1,n+1):
        request_data["page"] = i

        site = requests.get(GITHUB_SEARCH_API_URL + "?" + urlencode(request_data)).text

        repository_list = json.loads(site)["items"]

        for p in repository_list:
            yield p


def main():
    """
    When ran as script, downloads most starred repositories from Github and writes data to CSV
    :return:
    """

    with open(CSV_FILENAME, 'w', encoding='utf-8') as f:
        writer = csv.DictWriter(f, dialect='excel', fieldnames=['owner', 'name', 'language', 'stargazers_count',  'commit_count', 'branch_count', 'release_count', 'open_issues_count',  'watchers_count', 'contributor_count', 'forks_count', 'license', 'created_at', 'pushed_at', 'updated_at'], )
        writer.writeheader()

        for p in repository_generator(10):
            repository = fill_repository(p)
            writer.writerow(repository)

if __name__ == "__main__":
    main()
