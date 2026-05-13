function run_participant(path_input, path_output, participant_id)

  if isequal(participant_id, 'all')
    participants   = readtable(fullfile(path_output, 'participants.tsv'), 'filetype', 'text');
    participant_id = participants.participant_id;
  end

  if ~iscell(participant_id)
    participant_id = {participant_id};
  end

  for p = participant_id(:)'
    spm_preprocess(path_output, p{1});
  end

  % apply list of transformations to fMRIs
  path_anat = fullfile(path_subject, 'anat');
  path_func = fullfile(path_subject, 'func');
  list_files = dir(fullfile(path_func, 'sub*nii'));
  szFiles = size(list_files);
  
  for f = 1:szFiles(1)
    run_event = extractEvents(list_files(f).name);
    
    path_tsv = dir(fullfile(path_func, sprintf('*%s*events.tsv', run_event))); % please keep this, and don't do any hard coded indexing into file lists in order to identify the events.tsv file
    path_tsv = fullfile(path_tsv(1).folder, path_tsv(1).name);
    T = readtable(path_tsv, 'filetype', 'text', 'delimiter', '\t');
  
    levels = create_levelParameters(2, T.trial_type, T.onset, T.duration); % I did not understand what is the philosophy of the dataEvents function, and at least for me it did not work
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
