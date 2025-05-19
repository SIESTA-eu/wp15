function whitelist2vector(files)

% routine used to vectorize limo_outputs. This is used 
% for differentially privatize data (the pipeline acts on long
% vectors, concatenating results)
%
% FORMAT whitelist2vector(files)
%
% INPUT files is cell array of limo files to concatenate