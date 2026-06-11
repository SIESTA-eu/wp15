function spm_glmfit(path_output, participant_id, session_id)
 
% function to specify and fit a simple GLM, combining across runs within a
% session. Note, probably it would be more powerful (and correct) to create
% a supermodel, across session, but for now it's not worth the hassle.

if isequal(session_id, 'ses*')
  d = dir(fullfile(path_output, participant_id, 'ses*'));
  session_id = {d.name}';
end
if iscell(session_id)
  % recurse and loop across sessions
  for s = session_id(:)'
    spm_glmfit(path_output, participant_id, s{1});
  end
  return;
end

dspm = dir(fullfile(path_output, participant_id, session_id, 'func', 'SPM.mat'));
if ~isempty(dspm)
  spmmats = fullfile({dspm.folder}', {dspm.name}');
  for i = 1:numel(spmmats) 
    delete(spmmats{i});
  end
end

d1 = dir(fullfile(path_output, participant_id, session_id, 'func', '*_events.tsv'));
d2 = dir(fullfile(path_output, participant_id, session_id, 'func', 'swarsub*.nii'));
d3 = dir(fullfile(path_output, participant_id, session_id, 'func', 'rp_sub*.txt'));

assert(numel(d1)==numel(d2));
assert(numel(d1)==numel(d3)); 

% assume a 1-to-1 match of the files in order 
% d1: events
% d2: preprocessed functional data
% d3: motion regressors

fnames_tsv = fullfile({d1.folder}', {d1.name}');
fnames_nii = fullfile({d2.folder}', {d2.name}');
fnames_rgr = fullfile({d3.folder}', {d3.name}');
fnames     = [fnames_tsv';fnames_nii';fnames_rgr'];

% 
fmri_spec                = [];
fmri_spec.dir            = {fullfile(path_output, participant_id, session_id, 'func')};
fmri_spec.timing.units   = 'secs';
fmri_spec.timing.RT      = 2;
fmri_spec.timing.fmri_t  = 16;
fmri_spec.timing.fmri_t0 = 8;
fmri_spec.fact           = struct('name', {}, 'levels', {});
fmri_spec.bases.hrf.derivs = [0 0];
fmri_spec.volt           = 1;
fmri_spec.global         = 'None';
fmri_spec.mthresh        = -Inf;
fmri_spec.mask           = {[]};
fmri_spec.cvi            = 'FAST';

ix = 0;
for f = fnames
  % loop across runs
  ix = ix+1;

  T      = readtable(f{1}, 'filetype', 'text', 'delimiter', '\t');
  cnames = {'image' 'text'};
  for c = [1 2]
    cond(c).name     = cnames{c};
    cond(c).onset    = T.onset(T.trial_type==c);
    cond(c).duration = T.duration(T.trial_type==c);
    cond(c).orth     = [];
    cond(c).tmod     = 0;
    cond(c).pmod     = [];
  end
  fmri_spec.sess(ix).cond      = cond;
  fmri_spec.sess(ix).scans     = cellstr(spm_select('expand', f{2}));
  fmri_spec.sess(ix).regress   = struct('name', {}, 'val', {});
  fmri_spec.sess(ix).multi_reg = f(3);
  fmri_spec.sess(ix).multi     = {[]};
  fmri_spec.sess(ix).hpf       = 128;
end
out = spm_run_fmri_spec(fmri_spec);

% fit the model
fmri_est.spmmat           = out.spmmat;
fmri_est.write_residuals  = 0;
fmri_est.method.Classical = 1;
out                       = spm_run_fmri_est(fmri_est);

% compute the first-level image-text contrast
load(out.spmmat{1});

names = SPM.xX.name';
Cvec  = zeros(numel(names), 1);
Cvec(contains(names, 'image')) = 1;
Cvec(contains(names, 'text'))  = -1;

SPM.xCon = spm_FcUtil('Set', 'image-text', 'T', 'c', Cvec, SPM.xX.xKXs);
SPM      = spm_contrasts(SPM, 1);
