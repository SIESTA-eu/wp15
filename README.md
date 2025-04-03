# SIESTA - work package 15

This repository contains the work that is done in the context of work package 15, reflecting use case 2 about medical (neuro)imaging applications. It identifies representative datasets and defines some representative analysis pipelines.

## Use case overview

The use cases serve to get a broad and representative sample of neuroimaging datasets and analysis pipelines.

| Use case                     | Data type and source      | Transfer method | Analysis software     | Responsible partner |
|------------------------------|---------------------------|-----------------|-----------------------|---------------------|
| [2.1](usecase-2.1/README.md) | Tabular (OpenNeuro)       | wget            | R/Python/Julia/MATLAB | Nijmegen            |
| [2.2](usecase-2.2/README.md) | Anatomical MRI (OpenNeuro)| openneuro/cli   | Container             | Nijmegen            |
| [2.3](usecase-2.3/README.md) | MEG (OpenNeuro)           | datalad         | MATLAB                | Nijmegen            |
| [2.4](usecase-2.4/README.md) | EEG (OSF)                 | osfclient       | MATLAB                | Copenhagen          |
| [2.5](usecase-2.5/README.md) | Functional MRI (OpenNeuro)| AWS S3          | MATLAB                | Toulouse            |

Detailed documentation for each use case is provided in the corresponding directories.

General documentation aimed at SIESTA users and on the general computational workflowis provided in the [docs](docs) directory.
