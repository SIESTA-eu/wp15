% apply a list of transformations on nifti files and write results to the correct output directory
function patientsDatabase(path_input, path_output, level, sub_list, task_list)

  addpath('/work');

  if nargin<4 || isempty(sub_list) || (ischar(sub_list) && isequal(sub_list,'all'))
    list_subjects = dir(fullfile(path_input, 'sub*'));
    sub_list = {list_subjects.name}';
  end

  if nargin<5 || (ischar(task_list) && isequal(task_list, 'all'))
    task_list = {'DOTS_run-001' 'DOTS_run-002' 'Motion_run-001' 'Motion_run-002' 'spWM_run-001' 'spWM_run-002'}';
  end

  % Initialiser le tableau "keep"
  keep = true(size(sub_list));

  switch level
    case 'participant'

      for p = 1:numel(sub_list)
        % Chemin vers le fichier .tsv du patient
        path_patient_in = fullfile(path_input, sub_list{p});
        scansfile = fullfile(path_patient_in, [sub_list{p} '_scans.tsv']);

        % Vérification d'existence du fichier
        if ~exist(scansfile, 'file')
          fprintf('Fichier manquant : %s\n', scansfile);
          keep(p) = false;
          continue;
        end

        % Ouvrir le fichier
        fid = fopen(scansfile);
        if fid == -1
          fprintf('Erreur ouverture fichier : %s\n', scansfile);
          keep(p) = false;
          continue;
        end

        % Lire l'en-tête (on peut l'ignorer ici)
        header_line = fgetl(fid);

        % Initialiser la colonne
        column = {};

        % Lecture ligne par ligne
        while ~feof(fid)
          line = strtrim(fgetl(fid));
          if isempty(line)
            continue;
          end
          parts = strsplit(line);  % coupe sur espaces et/ou tabulations
          column{end+1,1} = parts{1};  % ne garde que la première colonne
        end

        fclose(fid);

        % Boucle sur les tâches à chercher
        for t = 1:numel(task_list)
          % Remplacement de contains par strfind + cellfun
          matches = ~cellfun(@isempty, strfind(column, task_list{t}));      
        % Mise à jour du keep uniquement si on a au moins une correspondance
        keep(p) = keep(p) && any(matches);    
        end
      end

      % only keep those subjects that have the specified tasks
      fprintf('keeping %d out of %d subjects for whom the requested task data is present\n', sum(keep), length(keep));
      sub_list = sub_list(keep);

      % first level model for the specified subjects
      for p = 1:numel(sub_list)
        path_patient_in = fullfile(path_input, sub_list{p});
        path_patient_out = fullfile(path_output, sub_list{p});
        onePatient(path_patient_in, path_patient_out);
      end
    
    case 'group'
      % second level analysis for the specified subjects
      secondLevel(path_input, path_output, task_list, sub_list);
  end
end