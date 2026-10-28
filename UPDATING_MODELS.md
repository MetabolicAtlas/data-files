# Updating an integrated model

This guide updates one integrated model (for example Human-GEM 1.19.0 to 2.0.0) in this repository, and checks the result before it is deployed. It is written so that a person or an automated agent can follow it step by step. This repository holds only data; the scripts are in [data-generation](https://github.com/MetabolicAtlas/data-generation) (`update/`, `maps/`, `check/`), and the workflows here run them from a checkout of it. The maps are made in the model's maps repository ([Human-maps](https://github.com/SysBioChalmers/Human-maps), [Yeast-maps](https://github.com/SysBioChalmers/Yeast-maps)); this repository copies them.

Update one model at a time, straight to its latest release. Metabolic Atlas serves only one version of each model, and the maps are not versioned, so intermediate releases never reach the site and need not be integrated. Stepping through them is only useful to find in which release a problem appeared: run the script with `--version` for each one.

The work has three parts:

0. **Update the maps repository** of the model to the new release. A workflow in the maps repository does this and opens a pull request there; merge it first.
1. **Update and check the data files.** `update/update_model.py` in data-generation does this. It needs no Docker and runs anywhere with Python and Node.js.
2. **Test a local deployment.** This needs Docker. Build the Metabolic Atlas stack with the new files, run its tests and look at the site.

## What the script does

`python update/update_model.py --model <Model> --version <x.y.z>`, run in data-generation, runs these steps on the data-files checkout next to it (or the one given with `--data-files`) and stops at the first one that needs a person:

| Step | What happens | Stops when |
| --- | --- | --- |
| 1. Baseline | Runs data-generation on the current files and keeps a copy of the current model files, so the new version can be compared with the old one | data-generation fails |
| 2. Download | Downloads `model/*.yml`, `genes.tsv`, `metabolites.tsv` and `reactions.tsv` of the release tag from `SysBioChalmers/<Model>` into `integrated-models/<Model>`, keeping the existing YAML file name (e.g. `yeastGEM.yml`) | the tag or a file is missing |
| 3. metaData | Writes `metaData` as a plain mapping (RAVEN 3 writes an `!!omap`, which data-generation cannot read), sets `short_name` to the folder name, quotes `version` and `date`, and carries over fields the previous copy had but the release lacks (`full_name`, `description`, `github`, `authors`, ...) | the version in the YAML differs from `--version`, or the date is not `YYYY-MM-DD` |
| 4. Tables | Checks that every row in the three TSV files has as many fields as the header | any row has the wrong number of fields |
| 5. Index | Sets `version` and `date` of the model in `integrated-models/integratedModels.json` | the model is not in the index |
| 6. Timeline | Writes the model's GitHub releases, up to this version, to `integrated-models/<Model>/gemRepository.json` | the release is not on GitHub |
| 7. Maps | Copies the maps and the lists of maps (`subsystemSVG.tsv`, `compartmentSVG.tsv`) from the model's maps repository (`--maps-repo`) into `svg/<Model>` and `integrated-models/<Model>`, and removes the maps in `svg/<Model>` that the maps repository lacks, except the custom maps in `customSVG.tsv` (see [Maps](#maps) below) | the README of the maps repository names another release than `--version`: nothing is copied and the exit status is 2 |
| 8. Generate and check | Runs data-generation on the updated files, then its `check/check_generated_data.py`, which compares every generated file with the model files and with the baseline | data-generation fails, or a hard check fails |

Exit status: `0` all hard checks passed, `1` data-generation or a hard check failed, `2` a manual fix is needed first, or the maps repository does not hold the maps of this release.

The script edits `integrated-models/<Model>/`, `integrated-models/integratedModels.json` and the maps in `svg/<Model>` of data-files, and nothing else; the script does not change the maps repository. Everything it generates goes to a work folder outside both repositories (default `model-update-work` next to data-files).

### Maps

The maps and the lists of maps come from the maps repository, where `maps/update_maps.py` of data-generation fitted them to the release (part 0). The model's custom maps (`customSVG.tsv`, such as Human-GEM's protein secretion map) are kept here and are not in the maps repository. `--skip-maps` leaves the maps unchanged; a model without a maps repository keeps its maps here; the workflow then passes `--skip-maps`. The maps are copied again on every run, also with `--keep-files`, so corrections to maps and lists belong in the maps repository.

## Automated updates

The workflow [`.github/workflows/update-model.yml`](.github/workflows/update-model.yml) runs part 1 in GitHub Actions, with the scripts of a data-generation checkout (`main` unless `data_generation_ref` says otherwise), and opens a pull request:

- **Daily**, it updates Human-GEM to its latest release, if that is newer than the integrated version and the README of Human-maps says that its maps match that release (merge the maps pull request of part 0 first).
- **Manually** (Actions tab, *Update integrated model*, *Run workflow*), it updates any model (`model`), to the latest or a given release (`version`). You can also set the data-generation branch or tag to use (`data_generation_ref`).
- **On `repository_dispatch`** of type `model-release` with `{"model": ..., "version": ...}`. A model repository's release workflow can send this, given a token with access to this repository.

The workflow does nothing when the model is up to date, when the README of the maps repository names another release than the latest one (the run then prints a notice that the maps pull request has to be merged first), or when a branch for the same model and version already exists (one made by hand counts too). Otherwise it pushes `auto/update-<model>-<version>` and opens a pull request. The description shows the script output and the check summary, then the commands and the checklist for part 2. When the update stopped (status 2) or a check failed (status 1), the pull request is a draft and the workflow run fails. To finish such an update:

1. Fix the files on the pull request's branch, as in step 4 or 5 below.
2. Run the workflow manually with `continue_branch` set to that branch.

The workflow checks the branch again without downloading, and updates the pull request. The full report is in the run's artifacts. Its commits are the release files, the index and timeline, and the maps copied from the maps repository.

Part 2 (the local deployment test) stays manual. Merge the pull request when its checklist is done.

## Prerequisites

Clone the three repositories next to each other; the scripts and the Metabolic Atlas helper scripts expect this layout:

```
work/
├── data-files/        this repository, with Git LFS files pulled
├── data-generation/   MetabolicAtlas/data-generation: the generator, and the update, map and check scripts
├── Human-maps/        SysBioChalmers/Human-maps (Yeast-maps for Yeast-GEM): the maps of the model
└── MetabolicAtlas/    MetabolicAtlas/MetabolicAtlas (optional for part 1; used to list stale test identifiers)
```

```bash
git clone https://github.com/MetabolicAtlas/data-files
git clone https://github.com/MetabolicAtlas/data-generation
git clone https://github.com/SysBioChalmers/Human-maps
git clone https://github.com/MetabolicAtlas/MetabolicAtlas
(cd data-files && git lfs install && git lfs pull)
(cd data-generation && yarn install --frozen-lockfile)
pip install -r data-generation/requirements.txt
```

You need:

- Node.js 12 or later and yarn 1.22 or later.
- Python 3.9 or later with the packages in data-generation's `requirements.txt`. The update script uses `PyYAML` and `PyGithub`.
- Git LFS. Without `git lfs pull` the SVG maps in data-files are pointer files; the script stops and says so. The maps repositories do not use Git LFS.
- A data-generation version that writes EC codes as `; `-separated strings and reads quoted TSV headers. The script warns if it does not.
- Optionally `GH_TOKEN`, a GitHub token with read access. Without it GitHub allows 60 API calls an hour, which is enough for one model.

## Part 0: update the maps repository

The maps are fitted to a release in the model's maps repository, [SysBioChalmers/Human-maps](https://github.com/SysBioChalmers/Human-maps) or [SysBioChalmers/Yeast-maps](https://github.com/SysBioChalmers/Yeast-maps). Each has a workflow `update-maps.yml`, which calls the reusable workflow `.github/workflows/update-maps.yml` of data-generation:

- **Daily**, it checks whether the model has a release newer than the one in the README of the maps repository ("The maps match **Human-GEM 2.1.1**.").
- **Manually** (Actions tab, *Update maps*, *Run workflow*), it fits the maps to a given release (`version`), or to the latest.

For a newer release it runs `maps/update_maps.py` of data-generation, pushes the branch `auto/maps-<model>-<version>` and opens a pull request in the maps repository. The script:

1. Adapts the lists `subsystemSVG.tsv` and `compartmentSVG.tsv` of the maps repository to the release. A subsystem or compartment that is gone loses its row and its map. One that is new, and that no row lists, gets a row and a blank map that the editor fills. One that no row lists and that the previous release already had stays unlisted. A listed subsystem that is gone and a new subsystem that share at least 80% of the gone one's reactions are reported as a possible rename; the lists treat them as a removal and an addition, so the old map is deleted and the new subsystem gets a blank map. The pull request lists these changes.
2. Fits every map to the release with `maps/mapedit.py`, keeping the drawing: identifiers follow the model; reactions and metabolites that are gone are removed; metabolites swapped in a reaction are relabelled; gene boxes follow the gene rules; reactions of a map's subsystem (or compartment) that are not drawn are added next to their metabolites, in free space or below the drawing; parts that share a metabolite are connected; and the background band follows the edges. The rules are listed in [maps/RULES.md](https://github.com/MetabolicAtlas/data-generation/blob/main/maps/RULES.md) in data-generation. Run again on its own maps with the same model, the editor changes nothing, so the pull request shows what the new release causes.
3. Writes the transport maps again from the release (`maps/transport_map.py`), together with their rows in `subsystemSVG.tsv`: a membrane can gain or lose a map when its reactions change.
4. Writes every listed map as SVG, SBGN-ML and Escher (JSON) into `subsystem/` and `compartment/`, validated as described in the README of data-generation, and sets the version in the README.

The pull request description gives the number of changes per rule and what is left for review. When a map or the transport maps could not be fitted, or a subsystem may have been renamed, the pull request is a draft, the workflow run fails, and the README keeps the old release, so that data-files does not accept the maps. To keep the drawing of a renamed subsystem, check out the branch locally, restore the old map file from the base commit, put the new subsystem name in its row of `subsystemSVG.tsv`, delete the blank map and its row, set the release in the README back to the previous one, and run `maps/update_maps.py` locally on the checkout with `--version` of the release (it fits the restored map, writes all formats and sets the release in the README). Push the result and mark the pull request as ready. Other problems are corrected on the branch by hand, followed by the release in the README. Open a few maps of the pull request, the ones with the most changes first, and merge it. A new compartment gets one blank map; dividing it into parts is a layout decision made by hand.

Yeast-GEM needs the annotation tables (`genes.tsv`, `metabolites.tsv`, `reactions.tsv`) in the `model/` folder of the release; the Yeast-maps workflow stops without them, creates no branch and fails on every daily run until a release has them. Disable the workflow in the Actions tab until then.

GitHub switches off scheduled workflows in a repository without activity for 60 days; when a release takes longer, enable the workflow again in the Actions tab, or start it by hand. Both maps repositories need the setting *Allow GitHub Actions to create and approve pull requests* (Settings, Actions, General). The workflows use the token of the workflow run and no secret.

To run it by hand, in the folder that holds data-generation, with the packages of its `requirements.txt`, `jsonschema` and a `GH_TOKEN` (without one GitHub allows 60 API calls an hour):

```bash
git clone https://github.com/SysBioChalmers/Human-maps
python data-generation/maps/update_maps.py --model Human-GEM --repo Human-maps --summary summary.md
cd Human-maps && git switch -c maps-2.1.2 && git add -A && git commit -m "feat: fit the maps to Human-GEM 2.1.2"
```

With the libsbgn schema saved as `data-generation/maps/schema/SBGN.xsd` (from https://raw.githubusercontent.com/sbgn/libsbgn/master/resources/SBGN.xsd), every SBGN-ML file is validated; the script stops if a file does not pass.

## Part 1: update and check the data files

### 1. Find the version to update to

```bash
cd data-generation
python update/fetch_release_data.py -s
```

This lists every integrated model with a newer release and the latest one, e.g. `Human-GEM can be updated: 1.19.0 => 2.1.0`. Update to that latest release.

### 2. Make a branch in data-files

```bash
git -C ../data-files switch main && git -C ../data-files pull
git -C ../data-files switch -c chore/update-human-gem-2.0.0
```

### 3. Run the script, in data-generation

```bash
python update/update_model.py --model Human-GEM --version 2.0.0 --maps-repo ../Human-maps
```

Use the repository name from `SysBioChalmers` for `--model`; it is also the folder name in `integrated-models`. `--maps-repo` is the checkout of the maps repository after part 0 (its default branch, with the pull request of the release merged). Without `--maps-repo` the script ends with status 2; `--skip-maps` leaves the maps unchanged on purpose. The run takes about a minute; data-generation itself takes about 10 seconds.

On a cluster, run it as a batch job rather than on a login node. A Slurm example:

```bash
#!/bin/bash
#SBATCH -n 1 -c 2
#SBATCH -t 00:30:00
module load nodejs
cd /path/to/work/data-generation
python update/update_model.py --model Human-GEM --version 2.0.0 --maps-repo ../Human-maps
```

The compute node needs internet access for steps 2 and 6.

### 4. If the script stops with status 2: fix the model files

The message says what to fix. The common case is a row with the wrong number of fields:

```
STOP: rows with the wrong number of fields (...):
  genes.tsv:2841 ENSG00000137714: 7 fields, header has 10
```

data-generation reads the tables by position, so such a row would put values in the wrong columns. For each listed row:

1. Look at the same row on the model's `develop` branch. If it has been corrected there, copy the corrected row.
2. Otherwise, if only trailing fields are missing, add them as empty fields: one `""` per missing field in a quoted table, or an empty field in an unquoted one.
3. If a field in the middle is missing, so that later values are shifted, put each value back in its column by hand. Leave a field empty if its value is unknown; never guess an identifier.
4. Note each corrected row for the commit message. If the row is still wrong on the model's `develop` branch, open an issue on the model repository.

Then rerun with `--keep-files`, which skips the download and keeps your fixes:

```bash
python update/update_model.py --model Human-GEM --version 2.0.0 --maps-repo ../Human-maps --keep-files
```

Other stops and what to do:

| Message | Fix |
| --- | --- |
| `... has uncommitted changes` | Start from a clean `integrated-models/<Model>`, or add `--keep-files` if the changes are your own fixes to this update |
| `the YAML says version X, not Y` | The release's metaData has the wrong version: check the tag, then edit `version` in the YAML and rerun with `--keep-files` |
| `metaData date ... is not YYYY-MM-DD` | Rerun with `--date YYYY-MM-DD`, using the release date |
| `node is not on PATH`, `run 'yarn install'` | Install or load Node.js; run `yarn install --frozen-lockfile` in data-generation |
| `the SVG maps are Git LFS pointers` | Run `git lfs pull` in data-files |
| `the maps repository holds the maps of X, not Y` (status 2) | Run part 0 for the release and merge its pull request, update the checkout of the maps repository, and rerun with `--keep-files` |
| `X.tsv is missing in model/ at <tag>, but integrated-models/<Model>/X.tsv has content` | The release has no annotation tables, but data-files has some (Yeast-GEM 9.1.1 uses those of yeast-GEM's `develop` branch). Empty the three files and rerun without `--keep-files`; the update then has no cross-references. To keep them, copy afterwards the tables of a `develop` commit whose ids match the release's, and rerun with `--keep-files` |

### 5. If the script ends with status 1: read the failed checks

The report is at `../model-update-work/<Model>-<version>/check_report.md`. Each failed check is a line starting with `- FAIL:`. If data-generation itself failed, its output is in `generate.log` in the same folder.

| Failed check or error | Usual cause | Fix |
| --- | --- | --- |
| data-generation: `subsystem "X" does not exist in the model` | A subsystem with a map was renamed or removed, and the lists of maps were not adapted | Check that the maps repository holds the maps of this release; the lists there follow the model (part 0) |
| data-generation: `TypeError ... geneSuffix` (or `reactionSuffix`, `compoundSuffix`) | The release added a cross-reference column that data-generation does not know (e.g. `metSeedID`) | Add the column to `identifiers.js` in data-generation |
| `every cross-reference column is known to identifiers.js` | Same as above | Same as above |
| `<component> cross-reference links` with many missing | A TSV header data-generation cannot read | Compare the header with the previous version |
| `subsystems`, `compartments` | A subsystem or compartment name data-generation turns into an unexpected id | Read the detail; usually a model issue to report upstream |
| `integratedModels.json ... matches the YAML` | Index and YAML disagree | Rerun the script with `--keep-files` |
| `SVG files are real files, not Git LFS pointers` | LFS files not pulled | `git lfs pull` |

After a fix, rerun with `--keep-files`.

### 6. Read the report

All hard checks must pass. Then read the rest of the report; nothing in it blocks the update, but each item should be understood:

- **Warnings (`- WARN:`)** are problems in the model data, such as one metabolite with different formulas in different compartments, or two subsystem names that differ only in case. The site shows one value. Report new ones to the model repository.
- **Reactions drawn on the maps** lists map reactions that are not in the model. After the maps step this should be empty; anything listed is a problem of the maps repository.
- **Data overlay** shows how many overlay identifiers still match the model.
- **Changes compared with ...** lists the change in every generated file and every cross-reference database, and the identifiers added and removed. Large drops that the release notes do not explain need a look.
- **Identifiers used in MetabolicAtlas tests and frontend** lists identifiers in the tests that are no longer in the model; those tests will need new identifiers.

A warning about EC codes under `annotation/ec-code` means the release stores EC numbers where data-generation does not read them. The site would show no EC numbers, so data-generation must be updated first.

### 7. Commit, in data-files

Commit in three steps, as earlier updates did:

```bash
cd ../data-files
git add integrated-models/<Model>/*.yml integrated-models/<Model>/genes.tsv integrated-models/<Model>/metabolites.tsv integrated-models/<Model>/reactions.tsv
git commit -m "chore: update <Model> to <version>"      # list hand-corrected rows in the message body
git add integrated-models/integratedModels.json integrated-models/<Model>/gemRepository.json
git commit -m "chore: update aggregated index of model versions"
git add svg/<Model> integrated-models/<Model>/subsystemSVG.tsv integrated-models/<Model>/compartmentSVG.tsv
git commit -m "chore: copy the <Model> maps of <version> from the maps repository"
```

Do not commit anything from the work folder.

## Part 2: test a local deployment

This needs a machine with Docker and `docker compose`, with ports 80, 7474 and 7687 free. Run the commands in bash from the `MetabolicAtlas` folder.

1. Set up the stack as described in [Get started](https://github.com/MetabolicAtlas/MetabolicAtlas#get-started) of the MetabolicAtlas README (`env-local.env`, `source proj.sh`). Run `yarn install --frozen-lockfile` in data-generation once before the first `build-stack`.
2. **Baseline:** with data-files and data-generation on `main`:
    ```bash
    source proj.sh
    build-stack && start-stack
    ma-exec api yarn test 2>&1 | tee ../test-before.log
    ```
3. **Updated data:** switch data-files (and data-generation, if it changed) to the update branch, then:
    ```bash
    stop-stack
    build-stack && start-stack
    ma-exec api yarn test 2>&1 | tee ../test-after.log
    ```
    `build-stack` runs data-generation and imports the result into the Neo4j image, so no separate import is needed. Do not run `import-neo4j-db` on a filled database: its first statement deletes everything in one transaction, which exceeds the 40 s transaction timeout and is rolled back. Do not use `clean-stack` either: it also deletes the Docker volumes, including the GotEnzymes database.

    If every API test suite fails before any test runs, with an error from `node-fetch`, the test setup itself is broken, not the data. `node-fetch` 3 is ESM-only and the Jest configuration does not transform it. Run both test runs with a local Jest configuration that transforms `node-fetch`, and do not commit it.
4. **Compare the logs.** The API tests contain fixed counts and identifiers that are not updated with every model release, so some tests fail before the update too. Only failures that appear in `test-after.log` and not in `test-before.log` matter. Each one is either an expected change (a count, a version or an identifier that changed with the release, see step 6 of part 1) or a problem to investigate. Update the expected values in the MetabolicAtlas tests in a separate pull request.
5. **Cypress:** Cypress is not a dependency of the frontend, so run it with npx from the `MetabolicAtlas` folder: `npx --yes cypress run --project frontend`. Without a display (a server, WSL), it needs Xvfb (`xvfb-run npx --yes cypress run --project frontend`). The fixtures are stubbed API responses, so identifiers in them do not matter. Some tests wait only 4 s for the map viewer and fail now and then on any version; rerun a failing spec before treating it as a problem, and compare with a run on the baseline.
6. **Look at the site** on `http://localhost`, with the updated model selected:
    - the model list shows the new version and date;
    - a reaction with several EC numbers shows each as its own link, and its references are listed;
    - a gene page shows its cross-references (Ensembl, UniProt, NCBI Gene, Protein Atlas);
    - a metabolite page shows name, formula and charge;
    - a subsystem map and a compartment map open, and clicking a reaction opens its panel;
    - the 3D viewer opens for a compartment;
    - for Yeast-GEM, the custom maps open; if one no longer matches, it may now be part of the model files;
    - each data overlay colours the maps (Human-GEM and Yeast-GEM have overlays);
    - search finds a gene symbol and an EC number;
    - Compare Models works with the updated model;
    - the GEM repository timeline ends at the new version.

When the deployment works, push the branch and open a pull request with the report summary: the result line, the warnings, and the changes table.

## Notes for automated runs

- Run the whole of part 1 unattended; stop and hand over at exit status `2` if a row cannot be fixed from a later release, or if a fix would change a value. Status `2` also means that the maps repository does not hold the maps of the release: merge its pull request, then rerun.
- Never edit model content beyond restoring fields to their columns. Corrections to the model belong in the model's own repository.
- Commit, push and open pull requests only when asked to.
- To start an update over, delete the work folder (`model-update-work` next to data-files) and discard the changes in `integrated-models/<Model>`.
