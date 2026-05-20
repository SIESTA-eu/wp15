function spm_preprocess(path_output, participant_id, session_id)

if nargin<3
  session_id = 'ses*';
end

% this function has been inspired by the equivalently named function in
% usecase 2.5. I removed the dependency on the matlabbatch system, and call
% the job specific SPM-functions directly

% realign -> note that the motion correction + reslicing probably may be
% improved by using the same reference volume across runs-within-session,
% or even across sessions. I don't know what the best practice is here
niftis = dir(fullfile(path_output, participant_id, session_id, 'func', 'sub-*.nii'));
niftis = fullfile({niftis.folder}', {niftis.name}');
%niftis = niftis(1:3);
realign(niftis);

% slice-timing correction
niftis = dir(fullfile(path_output, participant_id, session_id, 'func', 'rsub-*.nii'));
niftis = fullfile({niftis.folder}', {niftis.name}');
%niftis = niftis(1:3);
stc(niftis);

% coregister with the session specific anatomicals -> note this probably is
% not optimal in the intended analysis context since we want to accumulate
% the data across sessions in order to estimate the first level model. I
% would expect it to make more sense to coregister to a single reference
% anatomical image. 
niftis = dir(fullfile(path_output, participant_id, session_id, 'func', 'meansub-*.nii'));
niftis = fullfile({niftis.folder}', {niftis.name}');
anatomicals = dir(fullfile(path_output, participant_id, session_id, 'anat', 'sub-*.nii'));
anatomicals = fullfile({anatomicals.folder}', {anatomicals.name}');
%anatomicals = anatomicals(1);
coreg(anatomicals, niftis);

% segment + normalise the anatomicals -> note I don't know whether all anatomicals need
% to be segmented, or whether any of the anatomicals needs to be segmented
segmentation(anatomicals);

% normalise the functional data
niftis = dir(fullfile(path_output, participant_id, session_id, 'func', 'arsub-*.nii'));
niftis = fullfile({niftis.folder}', {niftis.name}');
anatomicals = dir(fullfile(path_output, participant_id, session_id, 'anat', 'y_sub-*.nii'));
anatomicals = fullfile({anatomicals.folder}', {anatomicals.name}');
%anatomicals = anatomicals(1);
%niftis = niftis(1);
normalisation(anatomicals, niftis);

niftis = dir(fullfile(path_output, participant_id, session_id, 'func', 'warsub-*.nii'));
niftis = fullfile({niftis.folder}', {niftis.name}');
smooth(niftis);

end

function realign(niftis)

% Eoptions
realign.eoptions.quality = 0.9;
realign.eoptions.sep = 4;
realign.eoptions.fwhm = 5;
realign.eoptions.rtm = 1;
realign.eoptions.interp = 2;
realign.eoptions.wrap = [0 0 0];
realign.eoptions.weight = '';

%Roptions
realign.roptions.which = [2 1];
realign.roptions.interp = 4;
realign.roptions.wrap = [0 0 0];
realign.roptions.mask = 1;
realign.roptions.prefix = 'r';

for f = 1:numel(niftis)
  fnms = cellstr(spm_select('expand', niftis{f}));

  %Add data to the job
  realign.data = {fnms(:)};
  
  % Run the realignment per run (job.trNOTE: is this optimal?)
  spm_run_realign(realign);
end

end

function stc(niftis)

for f = 1:numel(niftis)
  V = spm_vol(niftis{f});

  stc.nslices = V(1).dim(3);
  stc.tr = V(1).private.timing.tspace;
  stc.ta = stc.tr - stc.tr/stc.nslices;
  stc.refslice = stc.nslices./2;
  stc.so = 1:stc.nslices; % for this dataset there does not seem to be timing info in the json, so I assume this FIXME
  stc.scans = niftis(f);
  stc.prefix = 'a';

  % Run the slice timing correction per run
  spm_run_st(stc);

end
end

function coreg(anatomicals, niftis)

for f = 1:numel(niftis)
  % find the matching anatomical
  [p,ff,e] = fileparts(niftis{f});
  ff = split(ff, '_');
  sess_id = ff{2};
  
  coreg.ref    = anatomicals(find(contains(anatomicals, sess_id),1,'first'));
  coreg.source = niftis(f);
        
  % Eoptions
  coreg.eoptions.cost_fun = 'nmi';
	coreg.eoptions.sep = [4 2];
	coreg.eoptions.tol = [0.02 0.02 0.02 0.001 0.001 0.001 0.01 0.01 0.01 0.001 0.001 0.001];
	coreg.eoptions.fwhm = [7 7];
        
	% Run
  spm_run_coreg(coreg);
end
end

function segmentation(anatomicals)

for f = 1:numel(anatomicals)
  
    % Channel
    preproc.channel.biasreg = 0.001;
    preproc.channel.biasfwhm = 60;
    preproc.channel.write = [0 1];
    preproc.channel.vols = anatomicals(f);

    % Warp
    preproc.warp.reg = [0 0.001 0.5 0.05 0.2];
    preproc.warp.affreg = 'mni';
    preproc.warp.fwhm = 0;
    preproc.warp.samp = 3;
    preproc.warp.write = [1 1];

    tpmdir = fullfile(spm('dir'), 'tpm');
    preproc.tissue(1).tpm = {fullfile(tpmdir, 'TPM.nii,1')};
    preproc.tissue(1).ngaus = 1;
    preproc.tissue(1).native = [1 0];
    preproc.tissue(1).warped = [0 0];
    preproc.tissue(2).tpm = {fullfile(tpmdir, 'TPM.nii,2')};
    preproc.tissue(2).ngaus = 1;
    preproc.tissue(2).native = [1 0];
    preproc.tissue(2).warped = [0 0];
    preproc.tissue(3).tpm = {fullfile(tpmdir, 'TPM.nii,3')};
    preproc.tissue(3).ngaus = 2;
    preproc.tissue(3).native = [1 0];
    preproc.tissue(3).warped = [0 0];
    preproc.tissue(4).tpm = {fullfile(tpmdir, 'TPM.nii,4')};
    preproc.tissue(4).ngaus = 3;
    preproc.tissue(4).native = [1 0];
    preproc.tissue(4).warped = [0 0];
    preproc.tissue(5).tpm = {fullfile(tpmdir, 'TPM.nii,5')};
    preproc.tissue(5).ngaus = 4;
    preproc.tissue(5).native = [1 0];
    preproc.tissue(5).warped = [0 0];
    preproc.tissue(6).tpm = {fullfile(tpmdir, 'TPM.nii,6')};
    preproc.tissue(6).ngaus = 2;
    preproc.tissue(6).native = [0 0];
    preproc.tissue(6).warped = [0 0];

    % Run
    spm_preproc_run(preproc);

end
end

function normalisation(anatomicals, niftis)
  
for f = 1:numel(niftis)
  % find the matching anatomical
  [p,ff,e] = fileparts(niftis{f});
  ff = split(ff, '_');
  sess_id = ff{2};
  
  norm.subj.def        = {anatomicals(find(contains(anatomicals, sess_id),1,'first'))};
  norm.subj.resample   = cellstr(spm_select('expand', niftis{f}));
  norm.woptions.bb     = [-78 -112 -70; 78 76 85];
  norm.woptions.vox    = [2 2 2];
  norm.woptions.interp = 4;
  norm.woptions.prefix = 'w';

  spm_run_norm(norm);
end
end

function smooth(niftis)

for f = 1:numel(niftis)
  smooth.data = niftis(f);
  smooth.fwhm = [8 8 8];
  smooth.dtype = 0;
  smooth.prefix = 's';
  smooth.im = false; %???

  spm_run_smooth(smooth);
end
end
