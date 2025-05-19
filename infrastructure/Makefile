# Apptainer executable (use 'singularity' if Apptainer is not installed)
APPTAINER = apptainer

# Directory containing definition files
DEF_DIR = .

# Find all definition files (.def) in the definition directory
DEF_FILES = $(wildcard $(DEF_DIR)/*.def)

# Generate corresponding container names (.sif) from definition files
INFRASTRUCTURE = $(DEF_FILES:.def=.sif)
DOWNLOAD = download-2.1.sif download-2.2.sif download-2.3.sif download-2.4.sif download-2.5.sif
PIPELINE = pipeline-2.1.sif pipeline-2.2.sif pipeline-2.3.sif pipeline-2.4.sif pipeline-2.5.sif

# Build a specific type of containers
infrastructure: $(INFRASTRUCTURE)
download: $(DOWNLOAD)
pipeline: $(PIPELINE)

# Default target: build all containers
all: infrastructure download pipeline

# Generic rule to build a .sif container from a .def file
%.sif: %.def
	$(APPTAINER) build $@ $<

# Rules to build download containers
download-2.1.sif: ../usecase-2.1/download.def
	cd ../usecase-2.1 && $(APPTAINER) build ../infrastructure/$@ $<

download-2.2.sif: ../usecase-2.2/download.def
	cd ../usecase-2.2 && $(APPTAINER) build ../infrastructure/$@ $<

download-2.3.sif: ../usecase-2.3/download.def
	cd ../usecase-2.3 && $(APPTAINER) build ../infrastructure/$@ $<

download-2.4.sif: ../usecase-2.4/download.def
	cd ../usecase-2.4 && $(APPTAINER) build ../infrastructure/$@ $<

download-2.5.sif: ../usecase-2.5/download.def
	cd ../usecase-2.5 && $(APPTAINER) build ../infrastructure/$@ $<

# Rules to build pipeline containers
pipeline-2.1.sif: ../usecase-2.1/pipeline-r.def
	cd ../usecase-2.1 && $(APPTAINER) build ../infrastructure/$@ $<

pipeline-2.2.sif:
	cd ../usecase-2.2 && $(APPTAINER) pull  ../infrastructure/$@ docker://nipreps/mriqc:24.0.0

pipeline-2.3.sif: ../usecase-2.3/pipeline.def
	cd ../usecase-2.3 && $(APPTAINER) build ../infrastructure/$@ $<

pipeline-2.4.sif: ../usecase-2.4/pipeline.def
	cd ../usecase-2.4 && $(APPTAINER) build ../infrastructure/$@ $<

pipeline-2.5.sif: ../usecase-2.5/pipeline.def
	cd ../usecase-2.5 && $(APPTAINER) build ../infrastructure/$@ $<

# Clean up generated container files
clean:
	rm -f $(INFRASTRUCTURE) $(DOWNLOAD) $(PIPELINE)

# Phony targets (targets that are not files)
.PHONY: all clean
