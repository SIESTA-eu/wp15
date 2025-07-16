% estimate model function, the result is stored on save directory
function estimateModel(path_output)

        path_spmmat = fullfile(path_output, 'SPM.mat');

    % spmmat
    matlabbatch{1}.spm.stats.fmri_est.spmmat = cellstr(path_spmmat); %path_spmmat

    % write_residuals
    matlabbatch{1}.spm.stats.fmri_est.write_residuals = 0;

    % method
        matlabbatch{1}.spm.stats.fmri_est.method.Classical = 1;

        % run batch job
        spm_jobman('run', matlabbatch);
        clear matlabbatch;

    path_estimate = fullfile(path_output, 'estimate_model.mat');
    copyfile(path_spmmat, path_estimate);
end
