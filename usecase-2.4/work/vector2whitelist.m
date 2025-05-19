function vector2whitelist(data,filetypes)

% routine used to reformat a vectorized output into
% the expected limo files. This is used 
% for differentially privatize data (the pipeline acts on long
% vectors, concatenating results)
%
% FORMAT whitelist2vector(data,filetypes)
%
% INPUT data is the vector of differentially private data
%       files is cell array of limo files that were concatenated
