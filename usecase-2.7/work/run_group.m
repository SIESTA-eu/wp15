function run_group(path_input, path_output)

grouppath = fullfile(path_output, 'derivatives', 'group');
mkdir(grouppath);

dspm = dir(fullfile(grouppath, 'SPM.mat'));
if ~isempty(dspm)
  spmmats = fullfile({dspm.folder}', {dspm.name}');
  for i = 1:numel(spmmats) 
    delete(spmmats{i});
  end
end


% select the input files for the second level statistics
d = dir(fullfile(path_output, 'sub*', 'ses*', 'func', 'con*.nii'));
fnames = fullfile({d.folder}', {d.name}');
n = numel(fnames);

% generate the voxel mask
V_ref = spm_vol(fnames{1});
[X, Y, Z] = deal(V_ref.dim(1), V_ref.dim(2), V_ref.dim(3));
data = zeros(X, Y, Z, n);

for i = 1:n
  V = spm_vol(fnames{i});
  data(:,:,:,i) = spm_read_vols(V);
end

% === Build robust mask (keep voxels valid in ≥ 95% of images)
valid_voxels = ~isnan(data) & data ~= 0;
threshold = 0.95 * n;
mask_cum = sum(valid_voxels, 4) >= threshold;

fprintf('Common mask contains %d voxels.\n', nnz(mask_cum));

% === Save the mask
mask_vol = V_ref;
mask_vol.fname = fullfile(grouppath, 'mask_common.nii');
mask_vol.dt = [spm_type('uint8') 0];  % binary mask
spm_write_vol(mask_vol, uint8(mask_cum));

path_mask = mask_vol.fname;
fprintf('Common mask saved to: %s\n', path_mask);

% just to get things going, I treat each session's contrast file as a
% single input. Statistically this is of course incorrect, but the purpose
% of this pipeline is to demonstrate computational feasibility, not
% scientific correctness of what is going on inside it

% 1. Factorial design (one-sample t-test)
factorial_design.dir = {grouppath};
factorial_design.des.t1.scans = fnames;
factorial_design.masking.em = {path_mask}; % explicit mask
factorial_design.masking.im = 0;           % disable implicit mask
factorial_design.masking.tm.tm_none = 1;   % no threshold masking
factorial_design.multi_cov = [];
factorial_design.cov = [];
factorial_design.globalc.g_omit = 1;
factorial_design.globalm.glonorm = 1;
factorial_design.globalm.gmsca.gmsca_no = 1;
spm_run_factorial_design(factorial_design);

% 2. Model estimation
fmri_est.spmmat = {fullfile(grouppath, 'SPM.mat')};
fmri_est.method.Classical = 1;
fmri_est.write_residuals = 0;
spm_run_fmri_est(fmri_est);

% 3. Contrasts
con.spmmat = {fullfile(grouppath, 'SPM.mat')};
con.consess{1}.tcon.name = 'Main_Effect';
con.consess{1}.tcon.weights = 1;
con.consess{1}.tcon.sessrep = 'none';
con.consess{2}.tcon.name = 'Main_Effect_Minus';
con.consess{2}.tcon.weights = -1;
con.consess{2}.tcon.sessrep = 'none';
con.delete = 0;
spm_run_con(con);
