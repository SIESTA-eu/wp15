function run_pipeline(path_input, path_output, level, subjectlist, sessionlist)

if nargin<4 || isempty(subjectlist)
  subjectlist = 'all';
end

if nargin<5 || isempty(sessionlist)
  sessionlist = {'ses-01' 'ses-02' 'ses-03'};
end

time_start = tic;

% initialize spm12 via matlab
spm('defaults','fmri');
spm_jobman('initcfg');
spm_get_defaults('cmdline',true);

% create output architecture directory based on input directory, and copy
% over the data + unzip the nii.gz files
if ~exist(path_output, 'dir') || ~exist(fullfile(path_output, 'participants.tsv'), 'file')
  % either the folder does not exist, or the participants.tsv does not
  % exist. in the latter case, I assume that the data are not there either
  create_outputfolder(path_input, path_output);
end

switch level
  case 'participant'
    %run_participant(path_input, path_output, 'all');
    run_participant(path_input, path_output, subjectlist, sessionlist); % for now only run 3 subjects and 2 sessions
  case 'group'
    run_group(path_input, path_output);
end

time_end = toc(time_start);
disp(time_end);
