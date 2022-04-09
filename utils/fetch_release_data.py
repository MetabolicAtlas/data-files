#!/usr/bin/env python
"""Description:
    Fetch release data from Github and output the result in JSON format
"""
import os
import json
from github import Github

try:
    api_token = os.environ['GH_TOKEN']
except KeyError:
    api_token = None

g = Github(api_token)


def get_release_data(repo_name):
    """Get release data from Github"""
    repo = g.get_repo(repo_name)
    releases = repo.get_releases()
    gem_name = os.path.basename(repo_name)
    gem_data = {}
    for rel in releases:
        version = rel.tag_name.lstrip('v')
        gem_data[version] = {}
        gem_data[version]['title'] = rel.title
        gem_data[version]['id'] = f"{gem_name}-{version}"
        gem_data[version]['date'] = rel.published_at.strftime("%Y-%m-%d")
        gem_data[version]['tag_name'] = rel.tag_name
        gem_data[version]['link'] = rel.html_url
        gem_data[version]['version'] = rel.tag_name.lstrip('v')
        gem_data[version]['prerelease'] = rel.prerelease
    return gem_data


def get_integrated_gems_list(repo_name):
    """Get the list of integrated GEMS from Github"""
    repo = g.get_repo(repo_name)
    file_content = repo.get_contents("integrated-models/integratedModels.json")
    data = json.loads(file_content.decoded_content.decode())
    gems_list = []
    for item in data:
        gems_list.append(item['short_name'])
    return gems_list


def generate_data():
    """Fetch data from Github and output the result in JSON format"""
    owner = "SysBioChalmers"
    gems_list = get_integrated_gems_list("MetabolicAtlas/data-files")
    all_data = {}
    for gem_name in gems_list:
        repo_name = f"{owner}/{gem_name}"
        gem_release_data = get_release_data(repo_name)
        all_data[gem_name] = gem_release_data
    print(json.dumps(all_data, indent=2))


if __name__ == "__main__":
    generate_data()
