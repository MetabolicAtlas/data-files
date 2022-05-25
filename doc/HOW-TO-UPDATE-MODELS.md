## How to update integrated models manually

Since the format and content of the model files, such as the `metaData` section
and subsystem entries, are not completely clear for models provided at
[SysBioChalmers](https://github.com/SysBioChalmers), an fully automated method
to update all integrated models to the latest version is not available yet.
This document provides some instructions about how to update models manually.


It is strongly recommended to update one model a time.

- Get the list of the integrated models by listing the folder `./integrated-models/` in the repo `data-files`.

- Select a target model

- Skip if the target model in `data-files` is already the latest version
  compared to the model at [SysBioChalmers](https://github.com/SysBioChalmers)

- Clone the target model from [SysBioChalmers](https://github.com/SysBioChalmers).

- Check out the latest version.

- Copy the YAML file and all TSV files (inside the subfolder `model` to the
   folder `integrated-models/xxx-GEM` in the repo `data-files`, where `xxx-GEM`
   stands for the name of the target model. Note that for `Yeast-GEM`, you
   should rename `yeast-GEM.yml` to `yeastGEM.yml` after copying.

- Modify or add the entities for `short_name`, `data`, and `version` if they
   are missing or not with the desired format. 
   The `short_name` should be in the format `Human-GEM`, that is, with a `-` to
   separate the species name and the term `GEM`, and the first letter of the
   species should be capitalized.

- Update the entries `version` and `date` in the file
   `integrated-models/integratedModels.json` for the target model. Make
   sure the `version` and the `data` in the JSON file match the values in the
   YAML file.

- Run `./generate` in the repo `data-generation`. If there are any error
   messages, fix the model files according to the message. Repeat until no
   error message is shown with data generation

- Re-build and re-deploy the stack locally. Then run the test by 
   ```ma-exec api yarn test``` and play around with the web pages.
   If there are any abnormal behaviors of found. Try to solved it.
   Note that a few failed tests are expected since some of the components might
   be removed in the updated models.

- If everything works as expected, commit the changes and work on the next
   model.

