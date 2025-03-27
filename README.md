# SIESTA - work package 15

This repository contains the work that is done in the context of work package 15, reflecting use case 2 about medical (neuro)imaging applications. It identifies representative datasets and defines some representative analysis pipelines.

## Use case overview

The use cases serve to get a broad and representative sample of neuroimaging datasets and analysis pipelines.

| Use case | Data type and source      | Transfer method | Analysis software     | Responsible Partner |
|----------|---------------------------|-----------------|-----------------------|---------------------|
| 2.1      | Tabular (OpenNeuro)       | wget            | R/Python/Julia/MATLAB | Nijmegen            |
| 2.2      | Anatomical MRI (OpenNeuro)| openneuro/cli   | Container             | Nijmegen            |
| 2.3      | MEG (OpenNeuro)           | datalad         | MATLAB                | Nijmegen            |
| 2.4      | EEG (OSF)                 | osfclient       | MATLAB                | Copenhagen          |
| 2.5      | Functional MRI (OpenNeuro)| AWS S3          | MATLAB                | Toulouse            |

More detailed documentation is provided in the respective use cases and in the [docs](docs) directory.
