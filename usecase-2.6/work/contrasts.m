% apply some contrasts to SPM.mat file  
function contrasts(path_output)

        split_output = strsplit(path_output, '/');
        directory_name = split_output{end};

        path_spmmat = fullfile(path_output, 'SPM.mat');

        SPM_loaded = load(path_spmmat);

        matlabbatch{1}.spm.stats.con.spmmat = cellstr(path_spmmat);
        matlabbatch{1}.spm.stats.con.consess{1}.tcon.name = 'contrast';         % t Contrast
        matlabbatch{1}.spm.stats.con.consess{1}.tcon.weights = [-1 0 0 1]; %[0 0 0 1] 
        matlabbatch{1}.spm.stats.con.consess{1}.tcon.sessrep = 'none';

        spm_jobman('run', matlabbatch);
        clear matlabbatch;
end
