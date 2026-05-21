% create output architecture directory based on input directory, ideally
% this should be taken care of by code that is more BIDS savvy
% also, here the (potentially) zipped nifti files are copied over into the
% output folder, and unzipped.
function create_outputfolder(path_input, path_output)

% start at the top level
if ~exist(path_output, 'dir')
  mkdir(path_output);
end
if ~exist(fullfile(path_output, 'participants.tsv'), 'file')
  fnamein  = fullfile(path_input, 'participants.tsv');
  fnameout = fullfile(path_output, 'participants.tsv');
  copyfile(fnamein, fnameout);
end

participants  = readtable(fullfile(path_output, 'participants.tsv'), 'filetype', 'text');

% create the sub-<> folders
for participant_id = participants.participant_id'
  subfolder   = fullfile(path_output, participant_id);
  subfolderin = fullfile(path_input, participant_id);
  if ~exist(subfolder{1}, 'dir')
    mkdir(subfolder{1});
  end

  % recurse into the subfolders of subfolder
  d = dir(fullfile(subfolderin{1}, 'ses*'));
  sesfolders = {d.name}';
  for sesfolder = sesfolders(:)'
    if ~exist(fullfile(subfolder{1}, sesfolder{1}), 'dir')
      mkdir(fullfile(subfolder{1}, sesfolder{1}));
    end
    
    % recurse into the session specific folder
    for stuff = {'anat' 'func'}
      if exist(fullfile(subfolderin{1}, sesfolder{1}, stuff{1}), 'dir')
        stufffolder = fullfile(subfolder{1}, sesfolder{1}, stuff{1});
        if ~exist(stufffolder, 'dir')
          mkdir(stufffolder);
          d = dir(fullfile(subfolderin{1}, sesfolder{1}, stuff{1}, 'sub*'));
          filelist = fullfile({d.folder}', {d.name}');
          copy_and_unzip(filelist, stufffolder);
        end
      end
    end
  end
end

function copy_and_unzip(filelist, outputfolder)

for fname = filelist(:)'
  [p, f, e] = fileparts(fname{1});
  fprintf('copying %s to %s\n', [f,e], outputfolder);
  destination = fullfile(outputfolder, [f, e]);
  copyfile(fname{1}, destination);
  if isequal(e, '.gz')
    % it's a zipped file
    fprintf('unzipping...\n');
    gunzip(destination);
    delete(destination);
  end
end
