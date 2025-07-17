function path_mask = generate_mask(path_input, list_runs)
% generate_mask - Generates a common mask from the con_0001.nii files
% found in sub-*/<run>/ folders inside a given leave-one-out directory.
%
% INPUTS:
%   path_input  : path to one leave-one-out folder (e.g., 'leaveoneout-1')
%   list_runs   : cell array of run names (e.g., {'DOTS_run-001', 'VOE_run-001'})
%
% OUTPUT:
%   path_mask   : full path to the saved common mask (.nii)

    % === Collect all sub-* folders
    subj_dirs = dir(fullfile(path_input, 'sub-*'));
    con_files = {};

    for s = 1:numel(subj_dirs)
        subj_path = fullfile(path_input, subj_dirs(s).name);
        for r = 1:numel(list_runs)
            run_path = fullfile(subj_path, list_runs{r});
            con_file = fullfile(run_path, 'con_0001.nii');
            if exist(con_file, 'file')
                con_files{end+1} = con_file;
            else
                warning('Missing con_0001.nii: %s', con_file);
            end
        end
    end

    n_files = numel(con_files);
    if n_files == 0
        error('No con_0001.nii files found. Please check folder structure.');
    end

    fprintf('Found %d con_0001.nii files.\n', n_files);

    % === Load all volumes into a 4D array
    V_ref = spm_vol(con_files{1});
    [X, Y, Z] = deal(V_ref.dim(1), V_ref.dim(2), V_ref.dim(3));
    all_data = zeros(X, Y, Z, n_files);

    for i = 1:n_files
        V = spm_vol(con_files{i});
        data = spm_read_vols(V);
        all_data(:,:,:,i) = data;
    end

    % === Build robust mask (keep voxels valid in ≥ 95% of images)
    valid_voxels = ~isnan(all_data) & all_data ~= 0;
    threshold = 0.95 * n_files;
    mask_cum = sum(valid_voxels, 4) >= threshold;

    fprintf('Common mask contains %d voxels.\n', nnz(mask_cum));

    % === Save the mask
    mask_vol = V_ref;
    mask_vol.fname = fullfile(path_input, 'mask_common.nii');
    mask_vol.dt = [spm_type('uint8') 0];  % binary mask
    spm_write_vol(mask_vol, uint8(mask_cum));

    path_mask = mask_vol.fname;
    fprintf('Common mask saved to: %s\n', path_mask);
end
