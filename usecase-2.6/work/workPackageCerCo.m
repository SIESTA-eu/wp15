function workPackageCerCo(path_input, path_output, level, sub_list, task_list)

  addpath('/work');

  if nargin<4 || isempty(sub_list)
    sub_list = 'all';
  end

  if nargin<5 || isempty(task_list)
    task_list = 'all';
  end

  time_start = tic;

  % initialize spm12 via matlab
  spm('defaults','fmri');
  spm_jobman('initcfg');
  spm_get_defaults('cmdline',true);

  % create output architecture directory based on input directory
  if ~exist(path_output, 'dir')
    createDataStructure(path_input, path_output);
  end

  % apply a list of transformations to nifti files (anat + func)
  patientsDatabase(path_input, path_output, level, sub_list, task_list);

  time_end = toc(time_start);
  disp(time_end);
end
