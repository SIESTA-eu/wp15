function secondLevel(path_input, path_output, list_runs, list_subjects)

    % === Generate the common mask only once ===
    path_mask = fullfile(path_input, 'mask_common.nii');
    if ~exist(path_mask, 'file')
        path_mask = generate_mask(path_input, list_runs);  % ← One-time generation
    else
        fprintf('Mask already exists: %s\n', path_mask);
    end

    for r = 1:numel(list_runs)
        run_name = list_runs{r};
        outputdir = fullfile(path_output, 'group', run_name);
        if ~isfolder(outputdir)
            mkdir(outputdir);
        end

        % Build list of normalized files (con_0001.nii) for all subjects
        norm_files = cell(numel(list_subjects), 1);
        for s = 1:numel(list_subjects)
            norm_file = fullfile(path_input, list_subjects{s}, run_name, 'con_0001.nii');
            if exist(norm_file, 'file')
                norm_files{s} = norm_file;
            else
                error('Normalized file not found: %s', norm_file);
            end
        end

        path_mask = fullfile(path_input, 'mask_common.nii');

        % Prepare SPM batch
        matlabbatch = {};

        % 1. Factorial design (one-sample t-test)
        matlabbatch{1}.spm.stats.factorial_design.dir = {outputdir};
        matlabbatch{1}.spm.stats.factorial_design.des.t1.scans = norm_files;
        matlabbatch{1}.spm.stats.factorial_design.masking.em = {path_mask}; % explicit mask
        matlabbatch{1}.spm.stats.factorial_design.masking.im = 0;           % disable implicit mask
        matlabbatch{1}.spm.stats.factorial_design.masking.tm.tm_none = 1;   % no threshold masking

        % 2. Model estimation
        matlabbatch{2}.spm.stats.fmri_est.spmmat = {fullfile(outputdir, 'SPM.mat')};

        % 3. Contrasts
        matlabbatch{3}.spm.stats.con.spmmat = {fullfile(outputdir, 'SPM.mat')};
        matlabbatch{3}.spm.stats.con.consess{1}.tcon.name = 'Main_Effect';
        matlabbatch{3}.spm.stats.con.consess{1}.tcon.weights = 1;
        matlabbatch{3}.spm.stats.con.consess{1}.tcon.sessrep = 'none';

        matlabbatch{3}.spm.stats.con.consess{2}.tcon.name = 'Main_Effect_Minus';
        matlabbatch{3}.spm.stats.con.consess{2}.tcon.weights = -1;
        matlabbatch{3}.spm.stats.con.consess{2}.tcon.sessrep = 'none';

        % Run full batch (design + estimation + contrasts)
        spm_jobman('run', matlabbatch);
        clear matlabbatch;

        fprintf('Estimation completed for %s\n', run_name);
        
        % === Check presence of xVol ===
        spm_path = fullfile(outputdir, 'SPM.mat');
        if exist(spm_path, 'file')
            S = load(spm_path);
            if isfield(S, 'SPM') && isfield(S.SPM, 'xVol')
                fprintf('xVol is present in %s\n', spm_path);
                fprintf('Number of voxels: %d\n', size(S.SPM.xVol.XYZ, 2));
            else
                fprintf('xVol is MISSING in %s\n', spm_path);
            end
        else
            fprintf('SPM.mat file not found in %s\n', outputdir);
        end
    end
end
