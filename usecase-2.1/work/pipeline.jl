#!/usr/bin/env julia

# This pipeline computes averages from the participants.tsv file
#
# Use as 
#    ./pipeline.jl [options] <inputdir> <outputdir> <level>
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
# Copyright (C) 2024-2025, SIESTA workpackage 15 team

using ArgParse
using CSV
using DataFrames
using Statistics
using JSON3
using FilePathsBase

############################################################
# Parse the command line arguments
############################################################

function parse_commandline()
    s = ArgParseSettings()

    @add_arg_table s begin
        "inputdir"
            help = "the input directory"
            required = true
        "outputdir"
            help = "the output directory"
            required = true
        "level"
            help = "the analysis level, either 'participant' or 'group'"
            required = true
        "--start-idx"
            help = "index of the first participant to include, one-offset"
            arg_type = Int
            default = 0
        "--stop-idx"
            help = "index of the last participant to include, one-offset"
            arg_type = Int
            default = 0
        "--verbose", "-v"
            help = "give more verbose information for debugging"
            action = :store_true
    end

    return parse_args(s)
end

##########################################################################
# Compute the averages of the age, height, and weight of the participants
##########################################################################

function main(options)

    if haskey(options, "verbose") && options["verbose"]
        println("options =")
        display(options)
    end

    # Read the participants.tsv file into a DataFrame
    inputfile = joinpath(options["inputdir"], "participants.tsv")
    participants = CSV.read(inputfile, DataFrame; delim='\t', missingstring="n/a")

    if haskey(options, "verbose") && options["verbose"]
        println("data contains $(nrow(participants)) participants")
    end

    # Create the output directory and its parents if they don't exist
    mkpath(options["outputdir"])
    
    # Write the metadata about the dataset to a JSON file in line with the BIDS standard
    # https://bids-specification.readthedocs.io/en/stable/modality-agnostic-files.html#dataset-description
    dataset_description = Dict(
        "Name" => "SIESTA Use Case 2.1",
        "BIDSVersion" => "1.10.0",
        "DatasetType" => "derivative",
        "License" => "CC0", # same as input dataset
        "Authors" => ["SIESTA workpackage 15 team"],
        "Acknowledgements" => ["SIESTA workpackage 15 team"],
        "HowToAcknowledge" => ["Please cite the SIESTA paper"],
        "Funding" => ["Horizon Europe research and innovation programme grant agreement No. 101131957"],
        "ReferencesAndLinks" => ["https://eosc-siesta.eu", "https://github.com/SIESTA-eu/wp15"],
        "SourceDatasets" => [
            Dict(
                "DOI" => "10.18112/openneuro.ds004148.v1.0.1", # FIXME, the DOI of the input dataset should be inserted here
                "Version" => "1.0.1"
            )    
        ],
        "GeneratedBy" => [
            Dict(
                "Name" => "Julia version of SIESTA use case 2.1",
                "Description" => "This code computes averages from the participants.tsv file",
                "Version" => "x.y.z",     # FIXME, the tagged version number should be inserted here 
                "Container" => Dict(
                    "Type" => "apptainer",
                    "Tag" => "latest",    # FIXME, the tagged version number should be inserted here
                    "URI" => "oras://ghcr.io/siesta-eu/pipeline-2.1.sif:latest"
                )
            )
        ]
    )
    
    dataset_description_json = joinpath(options["outputdir"], "dataset_description.json")
    open(dataset_description_json, "w") do f
        JSON3.pretty(f, dataset_description)
    end
    
    # Select participants based on start-idx and stop-idx
    if haskey(options, "stop-idx") && options["stop-idx"] > 0
        participants = participants[1:options["stop-idx"], :]
    end
    if haskey(options, "start-idx") && options["start-idx"] > 0
        participants = participants[options["start-idx"]:end, :]
    end

    if haskey(options, "verbose") && options["verbose"]
        println("selected $(nrow(participants)) participants")
    end

    # Create the output directory and its parents if they don't exist
    mkpath(options["outputdir"])

    if haskey(options, "level") && options["level"] == "participant"
        println("nothing to do at the participant level, only creating participant-level output directories")
        for participant in eachrow(participants)
            participant_dir = joinpath(options["outputdir"], "$(participant.participant_id)")
            mkpath(participant_dir)
        end

    elseif haskey(options, "level") && options["level"] == "group"
        outputfile = joinpath(options["outputdir"], "derivatives", "group", "results.tsv")

        # Create the group output directory and its parents if they don't exist
        mkpath(joinpath(options["outputdir"], "derivatives", "group"))

        # Compute averages
        averagedAge    = mean(skipmissing(participants.age))
        averagedHeight = mean(skipmissing(participants.Height))
        averagedWeight = mean(skipmissing(participants.Weight))

        # Put the results in a DataFrame
        result = DataFrame(
            averagedAge = [averagedAge],
            averagedHeight = [averagedHeight],
            averagedWeight = [averagedWeight]
        )

        if haskey(options, "verbose") && options["verbose"]
            display(result)
        end

        # Write the results to a TSV file
        CSV.write(outputfile, result; delim='\t', writeheader=false)
    end # if level

end # function

##########################################################################
# execute the code if it is run as a script
##########################################################################

options = parse_commandline()
main(options)

