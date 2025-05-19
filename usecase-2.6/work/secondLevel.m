function secondLevel(path_input, path_output, list_runs, list_subjects)

  % Create the global output folder
  group_outputdir = fullfile(path_output, 'group');
  if ~isfolder(group_outputdir)
    mkdir(group_outputdir);
  end

  % For each run
  for r = 1:numel(list_runs)

    run_name = list_runs{r};
    outputdir = fullfile(group_outputdir, run_name);
    if ~isfolder(outputdir)
      mkdir(outputdir);
    end

    % Delete the old model if present
    if isfile(fullfile(outputdir, 'SPM.mat'))
      delete(fullfile(outputdir, 'SPM.mat'));
    end

    % Prepare paths for each subject
    con_files = cell(numel(list_subjects), 1);
    def_files = cell(numel(list_subjects), 1);

    %path_leaveoneout_input = strrep(path_output, 'output', 'input');
    struct_files = dir(path_input);
    % Keep only folders (not files)
    is_folder = [struct_files.isdir];
    % Exclude '.' and '..'
    valid_names = ~ismember({struct_files.name}, {'.', '..', 'derivatives'});
    % Combine both conditions
    keep = is_folder & valid_names;
    % Extract the names in a cell array
    list_subjects = {struct_files(keep).name};

    for s = 1:numel(list_subjects)
      subj = list_subjects{s};

      % Path to con_0001.nii
      con_files{s} = fullfile(path_input, subj, run_name, 'con_0001.nii');

      %con_files{s} = fullfile(strrep(path_output, 'output', 'input'), subj, run_name, 'con_0001.nii');

      %number_input = split(path_input, '-');  
      %number_input = number_input{2};     

      % Identify the number
      if subj(end) == 'b'
        number_subject = subj(end-3:end-1);
      else
        number_subject = subj(end-2:end);
      end

      tmp_anat = '';
     % Special cases for SAXNES
      if strfind(subj, 'SAXNES2s')
        if str2double(number_subject) <= 13
          final_number = num2str(str2double(number_subject));
          path_subject = regexprep(path_input, '-\d+$', ['-' final_number]);
          tmp_anat = strrep(path_subject, 'leaveoneout', 'singlesubject');
        end

        if str2double(number_subject) >= 14 && str2double(number_subject) <= 15
          number_input = num2str(str2double(number_subject) - 1);
          final_number = num2str(str2double(number_input));
          path_subject = regexprep(path_input, '-\d+$', ['-' final_number]);
          tmp_anat = strrep(path_subject, 'leaveoneout', 'singlesubject');
        end

        if str2double(number_subject) >= 17 && str2double(number_subject) <= 22
          number_input = num2str(str2double(number_subject) - 2);
          final_number = num2str(str2double(number_input));
          path_subject = regexprep(path_input, '-\d+$', ['-' final_number]);
          tmp_anat = strrep(path_subject, 'leaveoneout', 'singlesubject');
        end

        if str2double(number_subject) >= 24 && str2double(number_subject) <= 32
          number_input = num2str(str2double(number_subject) - 3);
          final_number = num2str(str2double(number_input));
          path_subject = regexprep(path_input, '-\d+$', ['-' final_number]);
          tmp_anat = strrep(path_subject, 'leaveoneout', 'singlesubject');
        end

      else
        if strfind(subj, 'SAXNESs')
          if str2double(number_subject) < 8
            number_input = num2str(str2double(number_subject) + 26); % 29 - 3
            final_number = num2str(str2double(number_input));
            path_subject = regexprep(path_input, '-\d+$', ['-' final_number]);
            tmp_anat = strrep(path_subject, 'leaveoneout', 'singlesubject');
          end

          if str2double(number_subject) > 8
            number_input = num2str(str2double(number_subject) + 25); %29 - 4
            final_number = num2str(str2double(number_input));
            path_subject = regexprep(path_input, '-\d+$', ['-' final_number]);
            tmp_anat = strrep(path_subject, 'leaveoneout', 'singlesubject');
          end
        end
      end

      path_anat = fullfile(tmp_anat, subj, 'anat');

      % Build the path to the deformation file
      yfile_struct = files(startsWith({files.name}, 'y') & endsWith({files.name}, '.nii'));

      if isempty(yfile_struct)
        error('Deformation file missing for subject %s', subj);
      end

      def_files{s} = fullfile(path_anat, yfile_struct(1).name);
    end

    %% Step 1: Normalization
    matlabbatch = {};
    for s = 1:numel(list_subjects)
      matlabbatch{s}.spm.spatial.normalise.write.subj.def = {def_files{s}};
      matlabbatch{s}.spm.spatial.normalise.write.subj.resample = {con_files{s}};
      matlabbatch{s}.spm.spatial.normalise.write.woptions.bb = [-78 -112 -70; 78 76 85];
      matlabbatch{s}.spm.spatial.normalise.write.woptions.vox = [2 2 2];
      matlabbatch{s}.spm.spatial.normalise.write.woptions.interp = 4;
    end

    spm_jobman('run', matlabbatch);

    %% Step 2: Second-level analysis (One-sample t-test)
    matlabbatch = {};  % Reset the batch
    ncon_files = cell(numel(list_subjects), 1);

    for s = 1:numel(list_subjects)
      norm_file = fullfile(path_input, list_subjects{s}, run_name, 'wcon_0001.nii');
      if exist(norm_file, 'file')
        ncon_files{s} = norm_file;
      else
        error('Normalized file not found: %s', norm_file);
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


