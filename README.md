## Data files for [MetabolicAtlas.org](https://metabolicatlas.org)

This repository centralizes data hosted in other repositories to facilitate the deployment of Metabolic Atlas. The long-term vision is to automate the deployment process by fetching the files directly, which would circumvent the need to duplicate files from these respositories.
The files in this repository are needed as input for [data-generation](https://github.com/metabolicatlas/data-generation) and the [source code of Metabolic Atlas](https://github.com/metabolicatlas/metabolicatlas).

This repository relies on [Git LFS](https://git-lfs.github.com/). It is recommended that Git LFS is installed before cloning this repository. The `svg` and `zip` files are stored with Git LFS.

For adding new a data source for data overlay, please refer to [this guide](DATA_OVERLAY.md).

## Licenses

The original licenses apply, as per the original repositories:

- [Fruitfly-GEM](https://github.com/SysBioChalmers/Fruitfly-gem)
- [Human-GEM](https://github.com/SysBioChalmers/Human-gem)
- [Mouse-GEM](https://github.com/SysBioChalmers/Mouse-gem)
- [Rat-GEM](https://github.com/SysBioChalmers/Rat-gem)
- [Worm-GEM](https://github.com/SysBioChalmers/Worm-gem)
- [Yeast-GEM](https://github.com/SysBioChalmers/yeast-gem)
- [Zebrafish-GEM](https://github.com/SysBioChalmers/Zebrafish-gem)
- [Human-maps](https://github.com/SysBioChalmers/Human-maps)
- [Yeast-maps](https://github.com/SysBioChalmers/Yeast-maps)

For the rest of the files, or in case of uncertainty, send an email to contact[at]metabolicatlas.org.

## How to update integrated models manually

This document provides some instructions about how to update models manually. Since the format and content of the model files, such as the `metaData` section and subsystem entries, are not completely clear for models provided at [SysBioChalmers](https://github.com/SysBioChalmers), a fully automated method to update all integrated models to the latest version is not available yet.

It is strongly recommended to update one model a time.

- Get a list of the models that can be updated 
  
  Install required Python packages by 

  ```
  pip install -r ./utils/requirements.txt
  ```

  and then run

  ```
  python ./utils/fetch_release_data.py -s
  ```
  The above command will output a list of models that can be updated, e.g.: 

  ```
  Yeast-GEM can be updated: 8.4.2 => 8.6.0
  Human-GEM can be updated: 1.10.0 => 1.11.0
  Mouse-GEM can be updated: 1.2.0 => 1.3.0
  Rat-GEM can be updated: 1.2.0 => 1.3.0
  Zebrafish-GEM can be updated: 1.1.0 => 1.2.0
  Fruitfly-GEM can be updated: 1.1.0 => 1.2.0
  Worm-GEM can be updated: 1.1.0 => 1.3.0
  ```

- Select a target model.

- Clone the target model from [SysBioChalmers](https://github.com/SysBioChalmers).

- Check out the latest version.

- Copy the YAML file and all TSV files (inside the subfolder `model`) to the folder `integrated-models/xyz-GEM` in the repo `data-files`, where `xyz-GEM` stands for the name of the target model. Note that for `Yeast-GEM`, you should rename `yeast-GEM.yml` to `yeastGEM.yml` after copying.
   
  For example you may run the following command for the Human-GEM model while you are at `data-files/integrated-models`:
  ```
  rsync -av ../../Human-GEM/model/*.yml ../../Human-GEM/model/*.tsv Human-GEM
  ```

- Modify or add the entities for `short_name`, `date`, and `version` if they are missing or not with the desired format. 
   The `short_name` should be in the format `Fruitfly-GEM`, that is, with a `-` to separate the species name and the term `GEM`; and the first letter of the species should be capitalized.

- Update the entries `version` and `date` in the file `integrated-models/integratedModels.json` for the target model. Make sure the `version` and the `date` in the JSON file match the values in the YAML file.

- Run `./generate` in the repo `data-generation`. If there are any error messages, fix the model files according to the message. Repeat until no error message is shown with data generation.

- Re-build and re-deploy the stack locally. Then run the test by ```ma-exec api yarn test``` and play around with the web pages. If there are any abnormal behaviors found, try to solve it. Note that a few failed tests are expected since some of the components might be removed in the updated models.

- Check if all custom maps work as expected, especially for the Yeast-GEM. If not, some of the custom maps might be integrated in the model files already. If this is the case, modify accordingly.

- If everything works as expected, commit the changes and work on the next model.

Finally, update the timeline of model history by

    ```
    python ./utils/fetch_release_data.py
    ```
