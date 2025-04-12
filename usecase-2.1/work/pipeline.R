#!/usr/bin/env Rscript

# This pipeline computes averages from the participants.tsv file
#
# Use as
#    ./pipeline.R [options] <inputdir> <outputdir> <level>
# where the input and output directory must be specified, and the
# level is either "group" or "participant".
#
# Optional arguments:
#   -h,--help           Show this help and exit.
#   --verbose           Enable verbose output.
#   --start-idx <num>   Start index for participant selection.
#   --stop-idx <num>    Stop index for participant selection.

# This code is shared under the CC0 license
#
# Copyright (C) 2024, SIESTA workpackage 15 team

# This part of the script deals with possibly missing packages on-the-fly:
# It downloads them and puts them in a tempdir + adds the tempdir to the path
tdir <- tempdir()
.libPaths(c(tdir, .libPaths()))

hasoptparse <- c("optparse") %in% rownames(installed.packages())
hasdplyr <- c("dplyr") %in% rownames(installed.packages())
if (!hasoptparse) {
  install.packages("optparse", lib = tdir, dependencies = TRUE, repos = "https://cloud.r-project.org")
}
if (!hasdplyr) {
  install.packages("dplyr", lib = tdir, dependencies = TRUE, repos = "https://cloud.r-project.org")
}

# Load the required package for the option parsing
library("optparse", warn.conflicts = FALSE)
# Load the required package for column selection
library("dplyr", warn.conflicts = FALSE)
# Load the required package for JSON writing
library("jsonlite", warn.conflicts = FALSE)

# Define the option parser
option_list <- list(
  make_option(c("-v", "--verbose"), action = "store_true", default = FALSE,
              help = "Print extra output"),
  make_option(c("--start-idx"), type = "integer", default = 0,
              help = "Start index for participant selection", metavar = "INTEGER"),
  make_option(c("--stop-idx"), type = "integer", default = 0,
              help = "Stop index for participant selection", metavar = "INTEGER")
)

# Parse the options
parser <- OptionParser(option_list = option_list,
                       usage = "usage: %prog [options] input output level",
                       description = "This pipeline computes averages from the participants.tsv file.")
arguments <- parse_args(parser, positional_arguments = 3)
opts <- arguments$options
args <- arguments$args

# Check if help was requested
if (opts$help) {
  print_help(parser)
  quit(status = 0)
}

# Assign positional arguments
inputdir <- args[1]
outputdir <- args[2]
level <- args[3]

# Print verbose output if requested
if (opts$verbose) {
  cat("Verbose mode enabled\n")
  cat("Input directory:", inputdir, "\n")
  cat("Output directory:", outputdir, "\n")
  cat("Level:", level, "\n")
  cat("Starting index:", opts$'start-idx', "\n")
  cat("Stopping index:", opts$'stop-idx', "\n")
}

# Create the output directory and its parents if they don't exist
dir.create(outputdir, recursive = TRUE, showWarnings = FALSE)

# Write the metadata about the dataset to a JSON file in line with the BIDS standard
# https://bids-specification.readthedocs.io/en/stable/modality-agnostic-files.html#dataset-description
dataset_description <- list(
  "Name" = "SIESTA Use Case 2.1",
  "BIDSVersion" = "1.10.0",
  "DatasetType" = "derivative",
  "License" = "CC0", # same as input dataset
  "Authors" = list("SIESTA workpackage 15 team"),
  "Acknowledgements" = list("SIESTA workpackage 15 team"),
  "HowToAcknowledge" = list("Please cite the SIESTA paper"),
  "Funding" = list("Horizon Europe research and innovation programme grant agreement No. 101131957"),
  "ReferencesAndLinks" = list("https://eosc-siesta.eu", "https://github.com/SIESTA-eu/wp15"),
  "SourceDatasets" = list(
    list(
      "DOI" = "10.18112/openneuro.ds004148.v1.0.1",
      "Version" = "1.0.1"
    )
  ),
  "GeneratedBy" = list(
    list(
      "Name" = "R version of SIESTA use case 2.1",
      "Description" = "This code computes averages from the participants.tsv file",
      "Version" = "x.y.z", # FIXME, the tagged version number should be inserted here
      "Container" = list(
        "Type" = "apptainer",
        "Tag" = "latest", # FIXME, the tagged version number should be inserted here
        "URI" = "oras://ghcr.io/siesta-eu/pipeline-2.1.sif:latest"
      )
    )
  )
)

dataset_description_json <- file.path(outputdir, 'dataset_description.json')
write(jsonlite::toJSON(dataset_description, auto_unbox = TRUE, pretty = TRUE), dataset_description_json)

# Read the input file
inputfile <- file.path(inputdir, "participants.tsv")

# Read table, deal with missing values
participants <- read.csv(inputfile, sep = "\t", na.strings = c("n/a"))

# Select the rows
if (opts$'stop-idx' > 0) {
  participants <- participants[1:opts$'stop-idx', ]
}
if (opts$'start-idx' > 0) {
  participants <- participants[opts$'start-idx':nrow(participants), ]
}

# Print some of the columns
if (opts$verbose) {
  print(participants %>% select(1:5))
}

# Create the output directory and its parents if they don't exist
dir.create(outputdir, recursive = TRUE, showWarnings = FALSE)

if (level == "participant") {
  print("Nothing to do at the participant level, only creating participant-level output directories")
  for (i in 1:nrow(participants)) {
    dir.create(file.path(outputdir, participants$participant_id[i]), recursive = TRUE, showWarnings = FALSE)
  }
} else if (level == "group") {
  outputfile <- file.path(outputdir, "group", "results.tsv")
  dir.create(file.path(outputdir, "group"), recursive = TRUE, showWarnings = FALSE)

  # Use the column names and capitalization from the original dataset
  # Ignore missing values
  averagedage <- mean(participants$age, na.rm = TRUE)
  averagedHeight <- mean(participants$Height, na.rm = TRUE)
  averagedWeight <- mean(participants$Weight, na.rm = TRUE)

  # Construct table with results
  result <- data.frame(averagedage, averagedHeight, averagedWeight)

  if (opts$verbose) {
    print(result)
  }

  # Write the results to disk
  write.table(result, file = outputfile, sep = "\t", col.names = FALSE, row.names = FALSE)
}