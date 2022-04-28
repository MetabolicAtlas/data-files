#!/usr/bin/env python
"""Description:
    Fetch release data from Github and output the result in JSON format
"""
import os
import sys
import json
import argparse
from github import Github


def writefile(content, outfile, mode='w', is_flush=False):
    """Write text to file"""
    try:
        fpout = open(outfile, mode)
        fpout.write(content)
        if is_flush:
            fpout.flush()
        fpout.close()
    except IOError:
        print(f"Failed to write to {outfile}", file=sys.stderr)


def get_release_data(repo_name, git_api):
    """Get release data from Github"""
    repo = git_api.get_repo(repo_name)
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


def get_integrated_gems_list(repo_name, git_api):
    """Get the list of integrated GEMS from Github"""
    repo = git_api.get_repo(repo_name)
    file_content = repo.get_contents("integrated-models/integratedModels.json")
    data = json.loads(file_content.decoded_content.decode())
    gems_list = []
    for item in data:
        gems_list.append(item['short_name'])
    return gems_list


def generate_data(git_api, basedir, is_dryrun):
    """Fetch data from Github and output the result in JSON format"""
    owner = "SysBioChalmers"
    gems_list = get_integrated_gems_list("MetabolicAtlas/data-files", git_api)
    all_data = {}
    for gem_name in gems_list:
        repo_name = f"{owner}/{gem_name}"
        gem_release_data = get_release_data(repo_name, git_api)
        all_data[gem_name] = gem_release_data
        outfile = os.path.join(basedir, 'integrated-models', gem_name,
                               'gemRepository.json')
        if not is_dryrun:
            writefile(json.dumps(all_data, indent=2), outfile)
            msg = f"Result file output to {outfile}"
        else:
            msg = f"DryRun: result file will be output to {outfile}"
        print(msg)


def main():
    """main procedure"""
    parser = argparse.ArgumentParser(
        description='Generate data for GEMs repository',
        formatter_class=argparse.RawDescriptionHelpFormatter
        )
    parser.add_argument('-d', '--dry', dest='is_dryrun', default=False,
                        help='do not save output to file',
                        action='store_true')

    args = parser.parse_args()
    is_dryrun = args.is_dryrun

    try:
        api_token = os.environ['GH_TOKEN']
    except KeyError:
        api_token = None

    git_api = Github(api_token)
    rundir = os.path.dirname(sys.argv[0])
    basedir = os.path.realpath(os.path.join(rundir, os.pardir))

    generate_data(git_api, basedir, is_dryrun)


if __name__ == "__main__":
    main()
