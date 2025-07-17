function normalisation(path_input)
    
    %con_path = fullfile(run_path, 'con_0001.nii');
    r_files = dir(fullfile(path_input, 'rsub*.nii'));
    y_files = dir(fullfile(path_input, 'y*.nii'));

    y_file = fullfile(path_input, y_files(1).name);
    r_file = fullfile(path_input, r_files(1).name);

    matlabbatch{1}.spm.spatial.normalise.write.subj.def = {y_file};
    matlabbatch{1}.spm.spatial.normalise.write.subj.resample = {r_file};
    %matlabbatch{1}.spm.spatial.normalise.write.subj.resample = {con_path};
    matlabbatch{1}.spm.spatial.normalise.write.woptions.bb = [-78 -112 -70; 78 76 85];
    matlabbatch{1}.spm.spatial.normalise.write.woptions.vox = [2 2 2];
    matlabbatch{1}.spm.spatial.normalise.write.woptions.interp = 4;

    spm_jobman('run', matlabbatch);
    clear matlabbatch;

 end
