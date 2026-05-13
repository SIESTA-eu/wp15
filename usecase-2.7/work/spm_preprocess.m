function spm_preprocess(path_output, participant_id)

% this function has been inspired by the equivalently named function in
% usecase 2.5. I removed the dependency on the matlabbatch system, and call
% the job specific SPM-functions directly

% realign
niftis = dir(fullfile(path_output, participant_id, 'ses*', 'func', 'sub-*.nii'));
niftis = fullfile({niftis.folder}', {niftis.name}');
niftis = niftis(1:3);
%realign(niftis);

% slice-timing correction
niftis = dir(fullfile(path_output, participant_id, 'ses*', 'func', 'rsub-*.nii'));
niftis = fullfile({niftis.folder}', {niftis.name}');
niftis = niftis(1:3);
%stc(niftis);

% coregister with the session specific anatomicals
niftis = dir(fullfile(path_output, participant_id, 'ses*', 'func', 'meansub-*.nii'));
niftis = fullfile({niftis.folder}', {niftis.name}');
anatomicals = dir(fullfile(path_output, participant_id, 'ses*', 'anat', 'sub-*.nii'));
anatomicals = fullfile({anatomicals.folder}', {anatomicals.name}');
anatomicals = anatomicals(1);
%coreg(anatomicals, niftis);


% segment the anatomicals
segmentation(anatomicals);

end

function realign(niftis)

% Eoptions
job.eoptions.quality = 0.9;
job.eoptions.sep = 4;
job.eoptions.fwhm = 5;
job.eoptions.rtm = 1;
job.eoptions.interp = 2;
job.eoptions.wrap = [0 0 0];
job.eoptions.weight = '';

%Roptions
job.roptions.which = [2 1];
job.roptions.interp = 4;
job.roptions.wrap = [0 0 0];
job.roptions.mask = 1;
job.roptions.prefix = 'r';

for f = 1:numel(niftis)
  fnms = cellstr(spm_select('expand', niftis{f}));

  %Add data to the job
  job.data = {fnms(:)};
  
  % Run the realignment per run (job.trNOTE: is this optimal?)
  spm_run_realign(job);
end

end

function stc(niftis)

for f = 1:numel(niftis)
  V = spm_vol(niftis{f});

  job.nslices = V(1).dim(3);
  job.tr = V(1).private.timing.tspace;
  job.ta = job.tr - job.tr/job.nslices;
  job.refslice = job.nslices./2;
  job.so = 1:job.nslices; % for this dataset there does not seem to be timing info in the json, so I assume this FIXME
  job.scans = niftis(f);
  job.prefix = 'a';

  % Run the slice timing correction per run
  spm_run_st(job);

end
end

function coreg(anatomicals, niftis)

for f = 1:numel(niftis)
  % find the matching anatomical
  [p,ff,e] = fileparts(niftis{f});
  ff = split(ff, '_');
  sess_id = ff{2};
  
  job.ref    = anatomicals(find(contains(anatomicals, sess_id),1,'first'));
  job.source = niftis(f);
        
  % Eoptions
  job.eoptions.cost_fun = 'nmi';
	job.eoptions.sep = [4 2];
	job.eoptions.tol = [0.02 0.02 0.02 0.001 0.001 0.001 0.01 0.01 0.01 0.001 0.001 0.001];
	job.eoptions.fwhm = [7 7];
        
	% Run
  spm_run_coreg(job);
end
end

function segmentation(anatomicals)

for f = 1:numel(anatomicals)
  
    % Channel
    job.channel.biasreg = 0.001;
    job.channel.biasfwhm = 60;
    job.channel.write = [0 1];
    job.channel.vols = anatomicals(f);

    % Warp
    job.warp.reg = [0 0.001 0.5 0.05 0.2];
    job.warp.affreg = 'mni';
    job.warp.fwhm = 0;
    job.warp.samp = 3;
    job.warp.write = [1 1];

    x = spm_get_defaults('old');
    job.tissue.tpm = x.preproc.tpm; % whatever, life's just to short but this seems to work
    
    % Run
    spm_preproc_run(job)

end
end