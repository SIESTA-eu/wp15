function patientsDatabase(path_input, path_output, level, sub_list, task_list)

  % Initialize subject list if empty or 'all'
  if nargin < 4 || isempty(sub_list) || (ischar(sub_list) && isequal(sub_list, 'all'))
    list_subjects = dir(fullfile(path_input, 'sub*'));
    sub_list = {list_subjects.name}';
  end

  % Initialize task list only if empty or 'all'
  if nargin < 5 || (ischar(task_list) && isequal(task_list, 'all'))
    switch level
      case 'participant'
        task_list = {};

        % For each subject, extract tasks from .tsv files in 'func' folder
        for p = 1:numel(sub_list)
          path_func = fullfile(path_input, sub_list{p}, 'func');

          if ~exist(path_func, 'dir')
            warning('No func folder for subject %s', sub_list{p});
            continue;
          end

          % Get all .tsv files in the 'func' folder
          tsv_files = dir(fullfile(path_func, '*.tsv'));

          for i = 1:length(tsv_files)
            task = extractEvents(tsv_files(i).name);
            if ~isempty(task)
              task_list{end+1} = task;
            end
          end
        end

        % Remove duplicate task names
        task_list = unique(task_list)';

      case 'group'
        % Manually define task list for group-level analysis
        task_list = {'DOTS_run-001','VOE_run-001', 'VOE_run-002', 'VOE_run-003', 'VOE_run-004'}';
    end
  end

  % Process depending on the selected analysis level
  switch level
    case 'participant'
      % First-level analysis for each subject
      for p = 1:numel(sub_list)
        path_patient_in = fullfile(path_input, sub_list{p});
        path_patient_out = fullfile(path_output, sub_list{p});
        onePatient(path_patient_in, path_patient_out);
      end

    case 'group'
      % Run second-level analysis
      secondLevel(path_input, path_output, task_list, sub_list);
      disp('Second-level analysis completed with common mask');
  end
end