function onePatient(path_subject, path_output)

  addpath('/work');

  spm_preprocess(path_subject, path_output);
  disp('preProcess is done !');

  path_anat = fullfile(path_subject, 'anat');
  path_func = fullfile(path_subject, 'func');
  list_files = dir(fullfile(path_func, 'sub*nii'));
  szFiles = size(list_files);

  for f = 1:szFiles(1)
    run_event = extractEvents(list_files(f).name);

    path_tsv = dir(fullfile(path_func, sprintf('*%s*events.tsv', run_event)));
    path_tsv = fullfile(path_tsv(1).folder, path_tsv(1).name);

    fid = fopen(path_tsv);
    data = dlmread(path_tsv, '\t');
    onset = data(:, 1);
    duration = data(:, 2);
    trial_type = data(:, 7);

    levels = create_levelParameters(2, trial_type, onset, duration);
    disp('specify first level is done !');

    path_run = fullfile(path_output, run_event);

    %Déplacement des fichiers y_*.nii et iy_*.nii dans func/
    y_file = dir(fullfile(path_anat, 'y*.nii'));
    path_y_file = fullfile(path_anat, y_file(1).name);
    iy_file = dir(fullfile(path_anat, 'iy*.nii'));
    path_iy_file = fullfile(path_anat, iy_file(1).name);

    copyfile(path_y_file, path_run);
    copyfile(path_iy_file, path_run);

    normalisation(path_run);
    disp('normalisation is done !');

    smooth(path_run);
    disp('smooth is done !');

    specifyGLMFirstLevel(path_run, levels);
    disp('specifyGLMFirstLevel is done !');

    estimateModel(path_run);
    disp('estimateModel is done !');

    contrasts(path_run);
    disp('contrasts is done !');
  end
end
