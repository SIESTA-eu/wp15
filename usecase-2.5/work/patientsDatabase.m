% apply a list of transformations on nifti files and write results to the correct output directory
function patientsDatabase(path_input, path_output, level, sub_list, task_list)

if nargin<4 || isempty(sub_list) || (ischar(sub_list) && isequal(sub_list,'all'))
  list_subjects = dir(fullfile(path_input, 'sub*'));
  sub_list = {list_subjects.name}';
end

if nargin<5 || (ischar(task_list) && isequal(task_list, 'all'))
  task_list = {'DOTS_run-001' 'DOTS_run-002' 'Motion_run-001' 'Motion_run-002' 'spWM_run-001' 'spWM_run-002'}';
end

% look through the subjects and tasks
keep = true(size(sub_list));
for p = 1:numel(sub_list)
  path_patient_in = fullfile(path_input, sub_list{p});
  scansfile = fullfile(path_patient_in, [sub_list{p} '_scans.tsv']);
  scanstable = readtable(scansfile, 'FileType','text', 'Delimiter', '\t');
  for t = 1:size(task_list, 1)
    keep(p) = keep(p) && any(contains(scanstable.filename, task_list{t}));
  end
end
% only keep those subjects that have the specified tasks
fprintf('keeping %d out of %d subjects for whom the requested task data is present\n', sum(keep), length(keep));
sub_list = sub_list(keep);

switch level
  case 'participant'
    % first level model for the specified subjects
    for p = 1:numel(sub_list)
      path_patient_in = fullfile(path_input, sub_list{p});
      path_patient_out = fullfile(path_output, sub_list{p});
      onePatient(path_patient_in, path_patient_out);
    end
  case 'group'
    % second level analysis for the specified subjects
    secondLevel_works(path_input, path_output, task_list, sub_list);
end

end
