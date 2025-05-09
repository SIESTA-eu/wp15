function secondLevel(path_input, path_output, list_runs, list_subjects)

  % Créer le dossier de sortie global
  group_outputdir = fullfile(path_output, 'group');
  if ~exist(group_outputdir, 'dir')
    mkdir(group_outputdir);
  end

  % Pour chaque run
  for r = 1:numel(list_runs)

    run_name = list_runs{r};
    outputdir = fullfile(group_outputdir, run_name);
    if ~exist(outputdir, 'dir')
      mkdir(outputdir);
    end

    % Supprimer ancien modèle si présent
    if exist(fullfile(outputdir, 'SPM.mat'), 'file')
      delete(fullfile(outputdir, 'SPM.mat'));
    end

    % Préparation des chemins pour chaque sujet
    con_files = cell(numel(list_subjects), 1);
    def_files = cell(numel(list_subjects), 1);

    path_leaveoneout_input = strrep(path_output, 'output', 'input');
    struct_files = dir(path_leaveoneout_input);
    % Garder uniquement les dossiers (pas les fichiers)
    is_folder = [struct_files.isdir];    
    % Exclure '.' et '..'
    valid_names = ~ismember({struct_files.name}, {'.', '..'});   
    % Combiner les deux conditions
    keep = is_folder & valid_names;   
    % Extraire les noms dans une cellstr
    list_subjects = {struct_files(keep).name};

    for s = 1:numel(list_subjects)
      subj = list_subjects{s};

      % Chemin vers con_0001.nii
      con_files{s} = fullfile(strrep(path_output, 'output', 'input'), subj, run_name, 'con_0001.nii');

      % Identifier le numéro
      if subj(end) == 'b'
        number = subj(end-3:end-1);
      else
        number = subj(end-2:end);
      end

      % Cas particuliers pour SAXNES
      if strfind(subj, 'SAXNES2s')
        if str2double(number) < 13
          new_number = number;
          final_number = num2str(str2double(new_number));
          path_input = regexprep(path_input, '-\d+-', ['-' final_number '-']);
        end 

        if str2double(number) > 13 && str2double(number) < 16
          new_number = num2str(str2double(number) - 1);
          final_number = num2str(str2double(new_number));
          path_input = regexprep(path_input, '-\d+-', ['-' final_number '-']);
        end 

        if str2double(number) > 16 && str2double(number) < 23
          new_number = num2str(str2double(number) - 2);
          final_number = num2str(str2double(new_number));
          path_input = regexprep(path_input, '-\d+-', ['-' final_number '-']);        
        end

        if str2double(number) > 23 && str2double(number) < 33
          new_number = num2str(str2double(number) - 3);
          final_number = num2str(str2double(new_number));
          path_input = regexprep(path_input, '-\d+-', ['-' final_number '-']);
        end

      else
        if strfind(subj, 'SAXNESs')
          if str2double(number) < 8
            new_number = num2str(str2double(number) + 26); % 29 - 3
            final_number = num2str(str2double(new_number));
            path_input = regexprep(path_input, '-\d+-', ['-' final_number '-']);
          end 

          if str2double(new_number) > 8
            new_number = num2str(str2double(number) + 25); %29 - 4
            final_number = num2str(str2double(new_number));
            path_input = regexprep(path_input, '-\d+-', ['-' final_number '-']);
          end
        end
      end

      %tokens = regexp(path_input, '-(\d+)-', 'tokens');

      %if ~isempty(tokens)
        %input_number = tokens{1}{1};
      %else
        %input_number = NaN;  % ou gérer l'erreur
      %end

      %if str2double(new_number) ~= str2double(input_number)
        %final_number = str2double(new_number);
        %final_number = num2str(final_number);
        %path_input = regexprep(path_input, '-\d+-', ['-' final_number '-']);
      %end

      path_anat = fullfile(strrep(path_input, 'output', 'input'), subj, 'anat');
      % Construire chemin vers le fichier de deformation
      yfile_struct = dir(fullfile(path_anat, 'y*.nii'));

      if isempty(yfile_struct)
        error('Fichier de déformation manquant pour le sujet %s', subj);
      end

      def_files{s} = fullfile(path_anat, yfile_struct(1).name);
    end

    %% Étape 1 : Normalisation
    matlabbatch = {};
    for s = 1:numel(list_subjects)
      matlabbatch{s}.spm.spatial.normalise.write.subj.def = {def_files{s}};
      matlabbatch{s}.spm.spatial.normalise.write.subj.resample = {con_files{s}};
      matlabbatch{s}.spm.spatial.normalise.write.woptions.bb = [-78 -112 -70; 78 76 85];
      matlabbatch{s}.spm.spatial.normalise.write.woptions.vox = [2 2 2];
      matlabbatch{s}.spm.spatial.normalise.write.woptions.interp = 4;
    end

    spm_jobman('run', matlabbatch);

    %% Étape 2 : Analyse de second niveau (One-sample t-test)
    matlabbatch = {};  % Réinitialiser le batch
    ncon_files = cell(numel(list_subjects), 1);

    for s = 1:numel(list_subjects)
      norm_file = fullfile(strrep(path_output, 'output', 'input'), list_subjects{s}, run_name, 'wcon_0001.nii');
      if exist(norm_file, 'file')
        ncon_files{s} = norm_file;
      else
        error('Fichier normalisé introuvable : %s', norm_file);
      end
    end

    matlabbatch{1}.spm.stats.factorial_design.dir = {outputdir};
    matlabbatch{1}.spm.stats.factorial_design.des.t1.scans = ncon_files;

    matlabbatch{2}.spm.stats.fmri_est.spmmat = {fullfile(outputdir, 'SPM.mat')};

    matlabbatch{3}.spm.stats.con.spmmat = {fullfile(outputdir, 'SPM.mat')};
    matlabbatch{3}.spm.stats.con.consess{1}.tcon.name = 'Main_Effect';
    matlabbatch{3}.spm.stats.con.consess{1}.tcon.weights = 1;
    matlabbatch{3}.spm.stats.con.consess{1}.tcon.sessrep = 'none';

    matlabbatch{3}.spm.stats.con.consess{2}.tcon.name = 'Main_Effect_Minus';
    matlabbatch{3}.spm.stats.con.consess{2}.tcon.weights = -1;
    matlabbatch{3}.spm.stats.con.consess{2}.tcon.sessrep = 'none';

    spm_jobman('run', matlabbatch);

  end
end



