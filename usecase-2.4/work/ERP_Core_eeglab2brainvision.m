% This code is shared under the CC0 license
%
% Copyright (C) 2024, SIESTA workpackage 15 team

% This script converts the data files in the original dataset from the EEGLAB format
% (*.set and *.fdt) to the BrainVision Core file format (*.vhdr, *.vmrk and *.eeg).
%
% The BrainVision Core file format is much simpler than the HDF5/MATLAB based EEGLAB
% file format and hence will be the first target for BIDScramble.

inputdir  = 'input_eeglab';
outputdir = 'input_brainvision';

warning('off', 'MATLAB:MKDIR:DirectoryExists');

d = dir(fullfile(inputdir, '**'));

for i=1:numel(d)

  if d(i).isdir
    continue
  end

  inputfile  = fullfile(d(i).folder, d(i).name);
  outputfile = strrep(inputfile, inputdir, outputdir);
  mkdir(fileparts(outputfile))

  if endsWith(inputfile, '.set')
    % convert the set+fdt file
    hdr = ft_read_header(inputfile);
    dat = ft_read_data(inputfile);
    [p, f, x] = fileparts(outputfile);
    outputfile = fullfile(p, [f '.eeg']);
    ft_write_data(outputfile, dat, 'header', hdr, 'dataformat', 'brainvision_eeg')
  elseif endsWith(inputfile, '.fdt')
    % skip, this contains the data that goes with the set file
  elseif endsWith(inputfile, '_scans.tsv')
    % skip, the filenames in these are not valid any more
  else
    % copy any other file
    copyfile(inputfile, outputfile);
  end
end
