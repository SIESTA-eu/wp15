# Data rights holder

The data rights holder is the person or organization responsible for the dataset. They decide under which conditions the dataset can be shared, with whom, and they are responsible for initiating the data transfer.

The platform operator and the data rights holder have to settle on a way to transfer the data. We refer to this as _uploading_ in case the platform operator creates an account on the SIESTA platform for the data rights holder and if the latter initiates and controls the transfer. We refer to this as _downloading_ if the data rights holder creates an account for the platform operator on their institutional system, and if the latter initiates and controls the transfer. In neither case is the data user involved in the data transfer.

## Data transfer into the system (import)

### Uploading the data by the data rights holder

The data rights holder can use the account and the data transfer mechanism provided by the SIESTA platform operator to upload the data.

### Downloading the data by the platform operator

The data rights holder can provide the platform operator with instructions and access to download the data from the institutional storage system. Besides providing an account to access the data for download and explaining how the data transfer works, the data rights holder must provide a method to check completeness and integrity of the data after transfer, for example by providing a [manifest file](https://en.wikipedia.org/wiki/Manifest_file) with checksums.

## Privacy considerations

### For the raw input data

It is the responsibility of the data rights holder to employ data minimization and to ensure that the dataset does not contain information that is not needed for subsequent analyses.

It is the responsibility of the platform owner to ensure that data users cannot access the input data, as that is assumed to contain sensitive information.

### For the scrambled data

The scrambled data is needed for the data user to implement and test their analysis pipeline. The scrambling of the data is done using tools such as [BIDScramble](https://github.com/SIESTA-eu/wp15/tree/main/BIDScramble) and [anjana-app](https://github.com/SIESTA-eu/anjana-app).

It is the responsibility of the data rights holder to ensure that data following scrambling does not contain identiiable information. The data rights holder can use tools such as [DatLeak](https://github.com/SIESTA-eu/DatLeak) and [pycanon](https://github.com/IFCA-Advanced-Computing/pycanon) to review the scrambled data prior to it being released.

### For the results from the pipeline

The scrambled data is anonymous, hence the pipeline applied to the scrambled data is also anonymous and its result can be shared without restrictions.

The direct output of the pipeline applied to the original input data cannot be guaranteed to be anonymous. Noise needs to be added to make the direct output differentially private.

## Differentially private output data

An appropriately calibrated amount of noise is added to the output data to ensure that it is differentially private. The differentially private result can subsequently be shared without restrictions.
