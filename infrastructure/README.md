# Infrastructure

This directory contains the container definition files that are generic and that apply to all use cases. These containers are the responsibility of the platform operator and are executed according to the documented computational [workflow](../docs/workflow.md).

## Building containers

The containers, including the infrastructure, download and pipeline ones, are automatically built by a GitHub action whenever a new tag is pushed to the repository. These containers are made available on the GitHub container registry and on the [packages](https://github.com/orgs/SIESTA-eu/packages?repo_name=wp15) page of the wp15 repository.

Since building all containers takes a lot of time, you can also build containers locally. The instructions for that are specified in the README files for the specific use cases. You can also use the `Makefile` that is provided in the infrastructure directory. It allows building one container, or all of them.

    cd infrastructure
    
    make download-2.1.sif # only make this specific download container
    make pipeline-2.1.sif # only make this specific pipeline container
    make scramble.sif     # only make this specific container

    make download         # build all containers of this type
    make pipeline         # build all containers of this type
    make infrastructure   # build all containers of this type

    make all              # build all containers

