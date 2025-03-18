# WP15 - medical imaging

_This contains the draft end-user documentation for the medical imaging use case. Eventually it should move elsewhere and be integrated with the other use cases._

The 2nd use case in the SIESTA project is on medical imaging and restricts its focus to neuroimaging. In SIESTA it is dealt with in work package 15. Hence sometimes we refer to it as "wp15" and at other moments as "usecase-2".

## Data

In this work package we distinguish four types of data:

1. Source or input data. This type of data typically concerns original data that, alongside features of scienctific interest, contains a rich set of _indirect_ personal data (but no _direct_ personal data). When combined with other data sources, indirect personal data may allow for re-identification of direct personal data (such as a subject's name or birthdate), and hence makes the input data unfit for unrestricted public sharing.
2. Scrambled or synthetic data. This type of data is derived from the input data, such that the indirect personal features have been removed (to a varying degree) from the data, while the scientific features of interest are preserved sufficiently to allow implementing and testing an analysis pipeline.
3. Results from the pipeline. The results of the pipeline applied to the scrambled data are available to the data user, but the results of the pipeline applied to the input data are not directly accessible.
4. Differentially private output data. This type of data results from applying the pipeline to the input data and adding enough noise to be differentially private. This data no longer contains any direct or indirect personal data and is therefore always fit for sharing externally.

## User roles

Permission for accessing data is defined by the role of the user. In this work package we distinguish three roles:

1. [Data rights holder](data_rights_holder.md)
2. [Data user](data_user.md)
3. [Platform operator](platform_operator.md)

Each of these roles has its own section in the documentation, please click on the respective links.

## Data flow

This can be conceived to be graphically depicted in a flowchart.

1. data rights holder -> makes input data available to the platform
2. data user -> initiates analysis project and requests access to the scrambled data
3. platform operator -> scrambles the original data
4. data rights holder (optional) -> grants permission for scrambled data to be disclosed
5. data user -> installs software and dependencies and interactively implements and tests analysis pipeline on scrambled data
6. data user -> requests the analysis pipeline to be executed on the input data
7. platform operator -> executes the analysis pipelines
8. data user -> requests access to the output data
9. data rights holder (optional) -> grants permission for output data to be disclosed

The review by the data rights holder prior to data disclosure in step 4 and 9 are optional, depending on the trust that the data rights holder puts in the process for generating the scrambled and the oputput data. There might be different levels of randomness implemented in the BIDScramble tool (and requested by the data rights holder), resulting in the scrambled data being somewhere along the scale of "anonymous" to "personal".

The implementation of the analysis pipeline on the scrambled data (step 5) could be done on the platform, but could also be done by the data user on their own computer after downloading the scrambled data. After implementing it locally, the pipeline is to be uploaded. The result of step 5 is that the pipeline is available on the platform as a container.

The data flow is further detailed in the [computational workflow](workflow.md) documentation.
