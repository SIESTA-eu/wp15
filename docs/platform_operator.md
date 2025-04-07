# Platform operator

The platform operator is the person or organization responsible for the SIESTA infrastructure. They take care of the secure storage and compute environment and allow "data rights holders" to upload data to the platform and "data users" to perform analyses on that data and to download the results.

Uploading is in general considered as "sending data away" over the network, whereas downloading is "receiving data".

SIESTA wp15 makes use of the [BIDS](https://bids.neuroimaging.io) (Brain Imaging Data Structure) standard, which is a formalized framework for organizing and describing neuroimaging and behavioral data in a consistent, machine-readable manner to facilitate data sharing and reproducibility.

The neuroimaging use cases in wp15 require the input data to be organized according to the [BIDS format](http://bids-standard.org/), and the analysis to be implemented as a containerized [BIDS application](https://doi.org/10.1371/journal.pcbi.1005209). It is possible to verify the validity of the input data with the [BIDS validator](https://bids-standard.github.io/bids-validator/).

## Storage requirements

The data rights holder should specify how large the dataset is that they want to have stored on the SIESTA system.

Since large amounts of data are expected to be transferred (many GB, over many files), the transfer may take a considerable time.

There should be a possibility to check the completeness and integrity of the transferred files, for example using a [manifest file](https://en.wikipedia.org/wiki/Manifest_file) containing checksums and an application like [md5sum](https://en.wikipedia.org/wiki/Md5sum).

The platform operator should get information from the data rights holder on:

- the total amount of data that is to be transferred (in GB or TB)
- the number of files and directories that the data comprises of
- a manifest file to check completeness and integrity after data transfer
- the retention period of the data on the SIESTA storage system

Besides storing the dataset, disk space should be made available to allow for intermediate and final results. The data user should specify the expected storage requirements of the analysis pipeline.

## Data transfer into the system (import)

The platform operator and the data rights holder have to settle on a way to transfer the data. We refer to this as _uploading_ in case the platform operator creates an account for the data rights holder on the SIESTA platform and if the data rights holder initiates and controls the transfer. We refer to _downloading_ if the data rights holder creates an account on their system for the platform operator, and if the latter initiates and controls the transfer.

### Uploading the data by the data rights holder

Assuming that the SIESTA platform implements a secure file transfer protocol that is accessible to the data rights holder, then the data rights holder can initiate the data transfer. The platform operator should provide upload instructions to the data rights holder.

### Downloading the data by the platform operator

Assuming that the SIESTA platform does _not_ (yet) implement a secure file transfer protocol accessible to the data rights holder, the data rights holder needs to give the platform operator access to the dataset and the platform operator initiates the transfer.

In the different use cases under wp15 we have identified different transfer mechanisms that data rights holders may use. Furthermore, there are a number of generic data transfer mechanisms that the data rights holders may use.

- OpenNeuro command-line interface
- OSF command-line interface
- DataLad (based on git-annex)
- AWS S3
- sftp
- scp
- GridFTP
- ftp
- webdav
- wget
- curl

Some of these allow for recursively downloading a directory containing files and subdirectories. Others are more suited for the download of a single file. In case the dataset being transferred is contained in a (potentially compressed) archive, such as a zip, tar, tgz, or rar file, the platform operator must "unzip" the dataset.

## Data transfer out from the system (export)

The data user might want to download the scrambled data for pipeline development on their local computer.

The data user will also want to download the results of the application of the pipeline on the sensitive input data.

## Computational requirements

A regular analysis on the dataset often involves two phases: computations at the "participant" level (looping over all subjects), followed by computations at the "group" level (aggregating results over subjects).

It is quite common that the participant-level computations result in intermediate data that is of a similar size as the original data. The "participant" level computations can in principle be parallelized over subjects. The "group" level computations usually do not involve or allow for parallel computation.

The data user decides on the analysis that is to be executed on the data. Hence, the data user must specify an estimate of the computational requirements. Some computations will scale linearly in time with the dataset size (for example 2x as many subjects in the dataset means 2x longer computations) but other computations will have a non-linear relationship to the dataset size.

The platform operator should get information from the data user on:

- the number of processes to run
- whether these run sequentially or in parallel
- the number of cores per process
- the amount of memory per process
- the amount of computational time per process

## Executing the computations

SInce the data user cannot have direct access to the sensitive data, the computation is to be initiated by the platform operator. Following the computations, the results are used to calibrate nosie and to prepare diofferentially private results. These are optionally reviewd by the data rights holder and subsequently shared with the data user.

The analysis is to be implemented by the data user as a containerized [BIDS application](https://doi.org/10.1371/journal.pcbi.1005209). To allow development, testing, and deployment on the compute environment of the data user, we have settled on [Apptainer](https://apptainer.org). If needed, the platform operator convert the Apptainer image into a Docker image.
