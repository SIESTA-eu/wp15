function secondLevel_works(path_input, path_output, list_runs, list_subjects)
    
  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  %% Make model: 2nd level One-sample t-test
  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
   
  % Initialize the batch
  %matlabbatch = cell(3 + numel(list_subjects),1);
  
  % Define output directory for second-level results
  outputdir = fullfile(path_output, 'group');
  if ~exist(outputdir, 'dir')
    mkdir(outputdir);
  end

  for r = 1:numel(list_runs)

    outputdir = fullfile(path_output, 'group', list_runs{r});
    if ~exist(outputdir, 'dir')
      mkdir(outputdir);
    end
  
    if exist(fullfile(outputdir,'SPM.mat'))
      % avoid request for user input before proceeding
      delete(fullfile(outputdir,'SPM.mat'));
    end
  
    con_files = cell(numel(list_subjects),1);
    ncon_files = cell(numel(list_subjects),1);
    def_files = cell(numel(list_subjects),1);
    
    matlabbatch = {}; % Reinitialize matlabbatch for normalisation

    % First step: Normalization of the con_0001.nii
    for s = 1:numel(list_subjects)
      % List of first-level contrast images
      con_files{s} = fullfile(path_output, list_subjects{s}, list_runs{r}, 'con_0001.nii');
      
      % Find the appropriate y*.nii file for normalisation
      anat_dir = fullfile(path_input, list_subjects{s}, 'anat');
      y_file_struct = dir(fullfile(anat_dir, 'y*.nii'));
      
      if ~isempty(y_file_struct)
        def_files{s} = fullfile(anat_dir, y_file_struct(1).name);  % Take the first one found
      else
        error('Aucun fichier y*.nii trouvé pour le sujet %s', list_subjects{s});
      end
      
      % Normalization setup
      matlabbatch{s}.spm.spatial.normalise.write.subj.def = {def_files{s}};
      matlabbatch{s}.spm.spatial.normalise.write.subj.resample = {con_files{s}};
      matlabbatch{s}.spm.spatial.normalise.write.woptions.bb = [-78 -112 -70; 78 76 85];
      matlabbatch{s}.spm.spatial.normalise.write.woptions.vox = [2 2 2];
      matlabbatch{s}.spm.spatial.normalise.write.woptions.interp = 4;
    end

    % Run normalization
    spm_jobman('run', matlabbatch);

    % Clear the batch for the next step
    clear matlabbatch

    % Reinitialize matlabbatch for the next step (second-level analysis)
    matlabbatch = {}; 

    % Second step: Specify the factorial design for the one-sample t-test
    % === Update the ncon_files after normalisation ===
    for s = 1:numel(list_subjects)
      norm_file = fullfile(path_output, list_subjects{s}, list_runs{r}, 'wcon_0001.nii');
      if exist(norm_file, 'file')
        ncon_files{s} = [norm_file];
      else
        error('Fichier %s introuvable. La normalisation a peut-être échoué.', norm_file);
      end
    end

    % Create the factorial design
    matlabbatch{1}.spm.stats.factorial_design.dir = {outputdir};
    matlabbatch{1}.spm.stats.factorial_design.des.t1.scans = ncon_files;

    path_spm_mat = fullfile(path_output, 'group', list_runs{r}, 'SPM.mat');
    if exist(path_spm_mat, 'file')
      delete(path_spm_mat);
    end

    % Model estimation
    matlabbatch{2}.spm.stats.fmri_est.spmmat = {fullfile(path_output, 'group', list_runs{r}, 'SPM.mat')};

    % Contrast manager (optional, to define contrasts at the second level)
    matlabbatch{3}.spm.stats.con.spmmat = {fullfile(path_output, 'group', list_runs{r}, 'SPM.mat')};
    matlabbatch{3}.spm.stats.con.consess{1}.tcon.name = 'Main_Effect';
    matlabbatch{3}.spm.stats.con.consess{1}.tcon.weights = 1;
    matlabbatch{3}.spm.stats.con.consess{1}.tcon.sessrep = 'none';
  
    matlabbatch{3}.spm.stats.con.consess{2}.tcon.name = 'Main_Effect_Minus';
    matlabbatch{3}.spm.stats.con.consess{2}.tcon.weights = -1;
    matlabbatch{3}.spm.stats.con.consess{2}.tcon.sessrep = 'none';

    % Run the second-level analysis
    spm_jobman('run', matlabbatch);
    
  end
end


