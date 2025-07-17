% apply first level function based on nifti files (rsub*) and their associated text files (produced by the spm_preprocess function)
function specifyGLMFirstLevel(path_run, struct_levels)

  disp(path_run);

  names = struct_levels.conditionEvent;

  % retrieve nifti files (rsub*) and their associated text files for each subject
  struct_rsub = dir(fullfile(path_run, 'swrsub*.nii'));
  struct_txt = dir(fullfile(path_run, '*_sub*.txt'));

  path_rsub = fullfile(struct_rsub.folder, struct_rsub.name);
  path_txt = fullfile(struct_txt.folder, struct_txt.name);

  % specify scans and multi_regression files
  matlabbatch{1}.spm.stats.fmri_spec.sess.scans = cellstr(path_rsub);
  matlabbatch{1}.spm.stats.fmri_spec.sess.multi_reg = cellstr(path_txt);

  % setup batch job structure
  % dir
  matlabbatch{1}.spm.stats.fmri_spec.dir = cellstr(path_run);

  % timing
  matlabbatch{1}.spm.stats.fmri_spec.timing.units = struct_levels.timing_units;
  matlabbatch{1}.spm.stats.fmri_spec.timing.RT = struct_levels.timing_RT;

  % convert to cell array if needed
  if ~iscell(names)
    names = cellstr(names);
  end
  unames = unique(names);

  if exist(fullfile(path_run,'SPM.mat'))
    delete(fullfile(path_run,'SPM.mat'));
  end

  for s = 1:numel(unames)
    name_event = unames(s);
    subOnset = struct_levels.conditionOnset(strcmp(names, unames(s)));
    subDuration = struct_levels.conditionDuration(strcmp(names, unames(s)));

    matlabbatch{1}.spm.stats.fmri_spec.sess.cond(s).name = char(name_event);
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond(s).onset = subOnset;
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond(s).duration = subDuration;
  end

  %run batch job
  spm_jobman('run',matlabbatch);
  clear matlabbatch;
end
