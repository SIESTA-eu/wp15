# WP15 - medical imaging

_This contains the draft end-user documentation for the medical imaging use case. Eventually it should move elsewhere and be integrated with the other use cases._

The 2nd use case in the [SIESTA](https://eosc-siesta.eu)  project is on medical imaging and restricts its focus to neuroimaging. In SIESTA it is dealt with in work package 15. Hence sometimes we refer to it as "wp15" and at other moments as "usecase-2".

## Scope

The [SIESTA](https://eosc-siesta.eu) project aims to develop and implement Secure Interactive Environments for SensiTive data Analytics. So it is about the **analysis** of **sensitive** data, not about straight-forward data sharing where one party uploads data and another party downloads that data. It is also not about a general-purpose data analysis platform for any type of data, but specifically for sensitive data.

For straight-forward data sharing you should look into research data repositories, such as [OpenNeuro](https://openneuro.org), [EBRAINS](https://search.kg.ebrains.eu/?category=Dataset), the [Radboud Data Repository](https://data.ru.nl), [Public-nEUro](https://publicneuro.eu), [DataVerse](https://dataverse.org/installations), or [Zenodo](https://zenodo.org). [Re3data](https://www.re3data.org) is a registry with many research data repositories.

For generic online platforms to analyze your own data or data that you have downloaded you can look at [Brainlife](https://brainlife.io/about/), the [NeuroScience Gateway](https://nsgprod.sdsc.edu:8443/portal2/login!input.action), or at local compute facilities offered at your institution.

## Data

The [GDPR](http://data.europa.eu/eli/reg/2016/679/oj) defines personal data as any information relating to an identified or identifiable natural person. Furthermore, the concepts of anonymous data are defined in the GDPR, where the difference with pseudonymised data is also established. Specifically, anonymized data are _outside_ the scope of the GDPR because they are not associated with identified or identifiable natural persons. However, pseudonymized data _are_ under the scope of this regulation.

GDPR further specifies _direct_ and _indirect_ identifiable data. The difference between these lies in how easily the information can identify an individual. Direct personal data explicitly identifies a person (e.g., name, passport number, email, or phone number). Indirect personal data (such as a physiological measurement or a brain scan) does not identify someone on its own but can do so when combined with other information, especially when it is unique to the person, long-term stable, and if matching data can be accessed in other databases (like fingerprints).

In this work package we deal with personal data that is acquired for research purposes, represented as digital datasets in which data from multiple individual participants is combined. Since the data is acquired for medical neuroimaging research purposes, we assume that it pertains to indirect personal data. Participants can be considered to represent individual records in the dataset. The data is assumed to be homogeneous, i.e., the same variables are collected for all participants.

We distinguish two representations of the data that serves as the input of the analysis pipeline:

1. Source or input data. This typically concerns unprocessed or minimally processed research data (such as EEG and MEG, MRI) and corresponds to the data of scienctific interest. This data contains a rich set of _indirect_ personal data (but no _direct_ personal data). When linked with other data sources, indirect personal data may allow for re-identification of direct personal data (such as a subject's name or birthdate), and hence makes the input data unfit for unrestricted public sharing.
2. Scrambled or synthetic input data. This type of data is derived from the input data, such that the indirect personal features have been removed (to a varying degree) from the data, while the scientific features of interest are preserved sufficiently to allow implementing and testing an analysis pipeline.

We distinguish three representations of the data that results as output from the analysis pipeline:

1. Results from the scrambled data. This follows from the pipeline evaluated on the scrambled data. Devpending on the amount of scrambling, this data may or may not be complete nonsense. It can however be used to evaluate whether the pipeline computations were performed correctly and to organize and identify the desired output data. The results of the pipeline applied to the scrambled data are directly available to the data user.
2. Actual results from the input data. The results of the pipeline applied to the input data are not guarateed to be anonymous or differentially private and hence are not to be made directly accessible.
3. Differentially private results. This type of data results from applying the pipeline to the input data and adding enough noise to be differentially private and to prevent any data leakage. This data no longer contains any direct or indirect personal data and is therefore always fit for sharing externally. The noise that is needed for differential privacy is determined using a resampling strategy.

## User roles

Permission for accessing data is defined by the role of the user. In this work package we distinguish three roles. For each of the roles we have provided specific documentation (see links below). If you fall within one of the specific roles, please read the documentation aimed at your role first. It may contribute to your overall understanding to subsequently also go over the documentation for the other roles.

1. [Data rights holder](data_rights_holder.md)
2. [Data user](data_user.md)
3. [Platform operator](platform_operator.md)

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
