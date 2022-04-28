#!/usr/bin/env python
"""Description:
    Fetch release data from Github and output the result in JSON format
"""
import os
import sys
import json
import argparse
from github import Github

# define data for externalParentId
EXT_PARENT_ID = {
        }

# define PMID for each specific release (if there is any)
RELEASE_PMID_DICT = {
        }

# define PMID for each GEM
GEM_PMID_DICT = {
        'Yeast-GEM': '31395883',
        'Human-GEM': '32209698',
        'Mouse-GEM': '34282017',
        'Rat-GEM': '34282017',
        'Zebrafish-GEM': '34282017',
        'Fruitfly-GEM': '34282017',
        'Worm-GEM': '34282017',
        }


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


def get_count(repo_name, api_token):
    """Get count for genes, reactions and metabolites"""
    # To be implemented
    return {}


def get_validation(repo_name, api_token):
    """Get quality score for the model"""
    # To be implemented
    return {}


def get_release_data(repo_name, git_api):
    """Get release data from Github"""
    repo = git_api.get_repo(repo_name)
    releases = repo.get_releases()
    gem_name = os.path.basename(repo_name)
    gem_data_list = []
    for rel in releases:
        if rel.prerelease:  # ignore pre releases
            continue
        version = rel.tag_name.lstrip('v')
        li = version.split('-')
        if len(li) > 1:  # ignore alpha or beta releases
            continue
        gem_data = {}
        rel_id = f"{gem_name}-{version}"
        gem_data['id'] = rel_id
        if rel_id in EXT_PARENT_ID:
            gem_data['externalParentId'] = EXT_PARENT_ID[rel_id]
        else:
            gem_data['externalParentId'] = []
        gem_data['releaseDate'] = rel.published_at.strftime("%Y-%m-%d")
        gem_data['releaseLink'] = rel.html_url
        if rel_id in RELEASE_PMID_DICT:
            gem_data['PMID'] = RELEASE_PMID_DICT[rel_id]
        elif gem_name in GEM_PMID_DICT:
            gem_data['PMID'] = GEM_PMID_DICT[gem_name]
        else:
            gem_data['PMID'] = ''
        gem_data['count'] = get_count(repo_name, git_api)
        gem_data['validation'] = get_validation(repo_name, git_api)
        gem_data_list.append(gem_data)

    # sort the releases in the ascending order
    gem_data_list = gem_data_list[::-1]

    return gem_data_list


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
    for gem_name in gems_list:
        repo_name = f"{owner}/{gem_name}"
        gem_release_data = get_release_data(repo_name, git_api)
        outfile = os.path.join(basedir, 'integrated-models', gem_name,
                               'gemRepository.json')
        if not is_dryrun:
            writefile(json.dumps(gem_release_data, indent=2), outfile)
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
