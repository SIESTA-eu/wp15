% apply a list of transformations on niftii files and written results to the correct output directory
function onePatient(path_subject, path_output)

  % apply list of transformations to fMRIs
  spm_preprocess(path_subject, path_output);
  disp('preProcess is done !');

  path_func = fullfile(path_subject, 'func');
  list_files = dir(fullfile(path_func, 'sub*nii'));
  szFiles = size(list_files);

  for f = 1:szFiles(1)
    run_event = extractEvents(list_files(f).name);
  
    path_tsv = dir(fullfile(path_func, sprintf('*%s*events.tsv', run_event))); % please keep this, and don't do any hard coded indexing into file lists in order to identify the events.tsv file
    path_tsv = fullfile(path_tsv(1).folder, path_tsv(1).name);
    T = readtable(path_tsv, 'filetype', 'text', 'delimiter', '\t');

    levels = create_levelParameters(2, 'intact', T.trial_type, T.onset, T.duration); % I did not understand what is the philosophy of the dataEvents function, and at least for me it did not work
    disp('specify first level is done !');

    path_run = fullfile(path_output, run_event);

    firstLevel_works(path_run, levels);
    disp('firstLevel is done !');

    estimateModel(path_run);
    disp('estimateModel is done !');

    contrasts(path_run);
    disp('contrasts is done !');

  end

  path_anat = fullfile(path_subject, 'anat');
  list_files = dir(path_anat);
  szFiles = size(list_files);

  for f = 3:szFiles(1)
    check_sub = startsWith(list_files(f).name, 'sub')|startsWith(list_files(f).name, 'y_sub')|startsWith(list_files(f).name, 'iy_sub');

    if check_sub == false
      path_file = fullfile(path_anat, list_files(f).name);
      delete(path_file);
    end
  end
end
