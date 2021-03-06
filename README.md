#### Data files for [MetabolicAtlas.org](https://metabolicatlas.org)

This repository relies on [Git LFS](https://git-lfs.github.com/). It is recommended that Git LFS is installed before cloning this repository. The `.tsv` files, like several other file formats, are stored with Git LFS. There are, however, TSV files that contain the mapping of the subsystems and compartments to SVG files. For easy diffing, these files have the extension `.tsv.plain` so that they are ignored by Git LFS.

This repository centralizes data hosted in other repositories to facilitate the deployment of Metabolic Atlas. The long-term vision is to automate the deployment process by fetching the files directly, which would circumvent the need to duplicate files from these respositories.
The files in this repository are needed as input for [neo4j-data-generation](https://github.com/metabolicatlas/neo4j-data-generation) and the [source code of Metabolic Atlas](https://github.com/metabolicatlas/metabolicatlas).


#### Licenses

The original licenses apply - see original repositories:
- [Human-GEM](https://github.com/sysbiochalmers/human-gem)
- [Mouse-GEM](https://github.com/sysbiochalmers/mouse-gem)
- [Rat-GEM](https://github.com/sysbiochalmers/rat-gem)
- [Yeast-GEM](https://github.com/sysbiochalmers/yeast-gem)
- [Human-maps](https://github.com/sysbiochalmers/human-maps)
- [Yeast-maps](https://github.com/sysbiochalmers/yeast-maps)

For the rest of the files, or in case of uncertainty, send an email to contact[at]metabolicatlas.org.
