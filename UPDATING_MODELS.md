# Updating an integrated model

This guide updates one integrated model (for example Human-GEM 1.19.0 to 2.0.0) in this repository, and checks the result before it is deployed. It is written so that a person or an automated agent can follow it step by step.

Update one model at a time, straight to its latest release. Metabolic Atlas serves only one version of each model, and the maps are not versioned, so intermediate releases never reach the site and need not be integrated. Stepping through them is only useful to find in which release a problem appeared: run the script with `--version` for each one.

The work has three parts:

1. **Update and check the data files.** `utils/update_model.py` does this. It needs no Docker and runs anywhere with Python and Node.js, including a cluster node.
2. **Test a local deployment.** This needs Docker. Build the Metabolic Atlas stack with the new files, run its tests and look at the site.
3. **Publish the maps** to the model's maps repository, after the update is merged. A workflow does this.

## What the script does

`utils/update_model.py --model <Model> --version <x.y.z>` runs these steps and stops at the first one that needs a person:

| Step | What happens | Stops when |
| --- | --- | --- |
| 1. Baseline | Runs data-generation on the current files and keeps a copy of the current model files, so the new version can be compared with the old one | data-generation fails |
| 2. Download | Downloads `model/*.yml`, `genes.tsv`, `metabolites.tsv` and `reactions.tsv` of the release tag from `SysBioChalmers/<Model>` into `integrated-models/<Model>`, keeping the existing YAML file name (e.g. `yeastGEM.yml`) | the tag or a file is missing |
| 3. metaData | Writes `metaData` as a plain mapping (RAVEN 3 writes an `!!omap`, which data-generation cannot read), sets `short_name` to the folder name, quotes `version` and `date`, and carries over fields the previous copy had but the release lacks (`full_name`, `description`, `github`, `authors`, ...) | the version in the YAML differs from `--version`, or the date is not `YYYY-MM-DD` |
| 4. Tables | Checks that every row in the three TSV files has as many fields as the header | any row has the wrong number of fields |
| 5. Index | Sets `version` and `date` of the model in `integrated-models/integratedModels.json` | the model is not in the index |
| 6. Timeline | Writes the model's GitHub releases, up to this version, to `integrated-models/<Model>/gemRepository.json` | the release is not on GitHub |
| 7. Maps | Fits the SVG maps in `svg/<Model>` to the new version with `utils/maps/mapedit.py` (see [Maps](#maps) below) | the maps are Git LFS pointers |
| 8. Generate and check | Runs data-generation on the updated files, then `check/check_generated_data.py` from data-generation, which compares every generated file with the model files and with the baseline | data-generation fails, or a hard check fails |

Exit status: `0` all hard checks passed, `1` data-generation or a hard check failed, `2` a manual fix is needed first.

The script edits only `integrated-models/<Model>/`, `integrated-models/integratedModels.json` and the maps in `svg/<Model>`. Everything it generates goes to a work folder outside the repository (default `../model-update-work`).

### Maps

The maps are edited in place, keeping their drawing: identifiers follow the model; reactions and metabolites that are gone are removed; metabolites swapped in a reaction are relabelled; gene boxes follow the gene rules; reactions of a map's subsystem (or compartment) that are not drawn are added next to their metabolites, in free space or below the drawing; parts that share a metabolite are connected; and the background band follows the edges. The rules are listed in `utils/maps/RULES.md`. The step writes to `<work>/<Model>-<version>-maps/`:

- `maps_summary.md`: the number of changes per rule, and what is left for review (also in the pull request description);
- `edited/changes.tsv`: every change, by map and rule;
- `edited/*.review.svg`: copies of the maps with the changes highlighted (the workflow keeps them as the `map-review` artifact).

Open a few review copies, the maps with the most changes first. Maps without compartment boxes (Yeast-GEM's) draw every compartment in one area, and their gene boxes show the gene name over its identifier; `--gene-label` sets this. With `--kegg-dir <cache>` (made by `utils/maps/kegg_fetch.py`), added reactions that a KEGG map of their subsystem shows keep KEGG's arrangement. `--skip-maps` leaves the maps unchanged. New maps (for a subsystem or compartment without one) are not made by this step; `utils/maps/newmap.py` makes a blank map to start from.

Transport maps (Human-GEM's "Transport: ..." maps, one per membrane) are not edited but written again from the new model with `utils/maps/transport_map.py`, together with their rows in `subsystemSVG.tsv`: a membrane can gain or lose a map when its number of reactions changes. To add transport maps to a model that has none, run `transport_map.py <yml> <model folder> <a subsystem map as template> svg/<Model> integrated-models/<Model>/subsystemSVG.tsv` once.

## Automated updates

The workflow [`.github/workflows/update-model.yml`](.github/workflows/update-model.yml) runs part 1 in GitHub Actions and opens a pull request:

- **Daily**, it updates Human-GEM to its latest release, if that is newer than the integrated version.
- **Manually** (Actions tab, *Update integrated model*, *Run workflow*), it updates any model (`model`), to the latest or a given release (`version`). You can also set the data-generation branch or tag to use (`data_generation_ref`).
- **On `repository_dispatch`** of type `model-release` with `{"model": ..., "version": ...}`. A model repository's release workflow can send this, given a token with access to this repository.

The workflow does nothing when the model is up to date, or when a branch for the same model and version already exists (one made by hand counts too). Otherwise it pushes `auto/update-<model>-<version>` and opens a pull request. The description shows the script output and the check summary, then the commands and the checklist for part 2. When the update stopped (status 2) or a check failed (status 1), the pull request is a draft and the workflow run fails. To finish such an update:

1. Fix the files on the pull request's branch, as in step 4 or 5 below.
2. Run the workflow manually with `continue_branch` set to that branch.

The workflow checks the branch again without downloading, and updates the pull request. The full report is in the run's artifacts.

Part 2 (the local deployment test) stays manual. Merge the pull request when its checklist is done.

## Prerequisites

Clone the three repositories next to each other; the script and the Metabolic Atlas helper scripts expect this layout:

```
work/
├── data-files/        this repository, with Git LFS files pulled
├── data-generation/   MetabolicAtlas/data-generation
└── MetabolicAtlas/    MetabolicAtlas/MetabolicAtlas (optional for part 1; used to list stale test identifiers)
```

```bash
git clone https://github.com/MetabolicAtlas/data-files
git clone https://github.com/MetabolicAtlas/data-generation
git clone https://github.com/MetabolicAtlas/MetabolicAtlas
(cd data-files && git lfs install && git lfs pull)
(cd data-generation && yarn install --frozen-lockfile)
pip install -r data-files/utils/requirements.txt
```

You need:

- Node.js 12 or later and yarn 1.22 or later. On a cluster with environment modules, for example `module load nodejs`.
- Python 3.9 or later with the packages in `utils/requirements.txt`. The script uses `PyYAML` and `PyGithub`, and the map editor `lxml`.
- Git LFS. Without `git lfs pull` the SVG maps are pointer files; the script stops and says so.
- A data-generation version that writes EC codes as `; `-separated strings and reads quoted TSV headers. The script warns if it does not.
- Optionally `GH_TOKEN`, a GitHub token with read access. Without it GitHub allows 60 API calls an hour, which is enough for one model.

## Part 1: update and check the data files

### 1. Find the version to update to

```bash
cd data-files
python utils/fetch_release_data.py -s
```

This lists every integrated model with a newer release and the latest one, e.g. `Human-GEM can be updated: 1.19.0 => 2.1.0`. Update to that latest release.

### 2. Make a branch

```bash
git switch main && git pull
git switch -c chore/update-human-gem-2.0.0
```

### 3. Run the script

```bash
python utils/update_model.py --model Human-GEM --version 2.0.0
```

Use the repository name from `SysBioChalmers` for `--model`; it is also the folder name in `integrated-models`. The run takes about a minute; data-generation itself takes about 10 seconds.

On a cluster, run it as a batch job rather than on a login node. A Slurm example:

```bash
#!/bin/bash
#SBATCH -n 1 -c 2
#SBATCH -t 00:30:00
module load nodejs
cd /path/to/work/data-files
python utils/update_model.py --model Human-GEM --version 2.0.0
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
python utils/update_model.py --model Human-GEM --version 2.0.0 --keep-files
```

Other stops and what to do:

| Message | Fix |
| --- | --- |
| `... has uncommitted changes` | Start from a clean `integrated-models/<Model>`, or add `--keep-files` if the changes are your own fixes to this update |
| `the YAML says version X, not Y` | The release's metaData has the wrong version: check the tag, then edit `version` in the YAML and rerun with `--keep-files` |
| `metaData date ... is not YYYY-MM-DD` | Rerun with `--date YYYY-MM-DD`, using the release date |
| `node is not on PATH`, `run 'yarn install'` | Install or load Node.js; run `yarn install --frozen-lockfile` in data-generation |
| `the SVG maps are Git LFS pointers` | Run `git lfs pull` in data-files |

### 5. If the script ends with status 1: read the failed checks

The report is at `../model-update-work/<Model>-<version>/check_report.md`. Each failed check is a line starting with `- FAIL:`. If data-generation itself failed, its output is in `generate.log` in the same folder.

| Failed check or error | Usual cause | Fix |
| --- | --- | --- |
| data-generation: `subsystem "X" does not exist in the model` | A subsystem with a map was renamed or removed | Edit the row in `integrated-models/<Model>/subsystemSVG.tsv` (rename it, or delete the row if the subsystem is gone); the SVG file stays |
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
- **Reactions drawn on the maps** lists map reactions that are not in the model. After the maps step this should be empty; anything listed is in the map summary's review items.
- **Data overlay** shows how many overlay identifiers still match the model.
- **Changes compared with ...** lists the change in every generated file and every cross-reference database, and the identifiers added and removed. Large drops that the release notes do not explain need a look.
- **Identifiers used in MetabolicAtlas tests and frontend** lists identifiers in the tests that are no longer in the model; those tests will need new identifiers.

A warning about EC codes under `annotation/ec-code` means the release stores EC numbers where data-generation does not read them. The site would show no EC numbers, so data-generation must be updated first.

### 7. Commit

Commit in two steps, as earlier updates did:

```bash
git add integrated-models/<Model>/*.yml integrated-models/<Model>/*.tsv
git commit -m "chore: update <Model> to <version>"      # list hand-corrected rows in the message body
git add integrated-models/integratedModels.json integrated-models/<Model>/gemRepository.json
git commit -m "chore: update aggregated index of model versions"
git add svg/<Model>
git commit -m "feat: fit the <Model> maps to <version>"
```

Commit an edit to `subsystemSVG.tsv` or `compartmentSVG.tsv` separately, e.g. `fix: remove SVGs for subsystems deleted from <Model>`. Do not commit anything from the work folder.

## Part 2: test a local deployment

This needs a machine with Docker and `docker compose`, with ports 80, 7474 and 7687 free. Run the commands in bash from the `MetabolicAtlas` folder.

1. Create the environment file: `cp env-local.env.sample env-local.env`, and set `NEO4J_PASSWORD` and `POSTGRES_PASSWORD`. Run `yarn install --frozen-lockfile` in data-generation once before the first `build-stack`.
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

## Part 3: publish the maps

The repositories [SysBioChalmers/Human-maps](https://github.com/SysBioChalmers/Human-maps) and [SysBioChalmers/Yeast-maps](https://github.com/SysBioChalmers/Yeast-maps) hold the maps of `svg/<Model>` as SVG, SBGN-ML, SBML (with layout and groups), Escher maps (JSON) and PNG. Once an update is merged, the workflow `.github/workflows/publish-maps.yml` writes the maps in those formats with `utils/maps/publish_maps.py`, pushes branch `auto/maps-<model>-<version>` to the maps repository and opens a pull request there. Review it (the PNG images show the maps) and merge it.

The workflow needs the repository secret `MAPS_REPOS_TOKEN`: a token of an account with write access to both maps repositories (a fine-grained token with Contents and Pull requests read and write, on those two repositories). It can also be started by hand from the Actions tab, for one model.

To publish by hand, with python-libsbml, lxml, cairosvg, Pillow and jsonschema installed:

```bash
git clone https://github.com/SysBioChalmers/Human-maps
python data-files/utils/maps/publish_maps.py --model Human-GEM --repo Human-maps --summary summary.md
cd Human-maps && git switch -c maps-2.1.0 && git add -A && git commit -m "feat: maps for Human-GEM 2.1.0"
```

With the libsbgn schema saved as `utils/maps/schema/SBGN.xsd` and Escher's map schema as `utils/maps/schema/escher_1-0-0.json` (from https://escher.github.io/escher/jsonschema/1-0-0, with `jsonschema` installed), every SBGN-ML file and Escher map is validated against them; every SBML file is checked with libsbml, and every Escher map with Escher's own consistency checks. The script stops if a file does not pass.

## Notes for automated runs

- Run the whole of part 1 unattended; stop and hand over at exit status `2` if a row cannot be fixed from a later release, or if a fix would change a value.
- Never edit model content beyond restoring fields to their columns. Corrections to the model belong in the model's own repository.
- Commit, push and open pull requests only when asked to.
- To start an update over, delete the work folder (`../model-update-work`) and discard the changes in `integrated-models/<Model>`.
