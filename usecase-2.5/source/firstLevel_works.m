% apply first level function based on nifti files (rsub*) and their associated text files (produced by the spm_preprocess function)
function firstLevel_works(path_run, struct_levels)

names = struct_levels.conditionName;
split_names = split(names, '_');
szSplit = size(split_names);
sz_split = szSplit(1) - 1;

index_onset = 1;
index_duration = 1;

save_onset = 1;
save_duration = 1;

% retrieve nifti files (rsub*) and their associated text files for each subject
struct_rsub = dir(fullfile(path_run, 'rsub*'));
struct_txt = dir(fullfile(path_run, '*.txt'));

path_rsub = fullfile(struct_rsub.folder, struct_rsub.name);
path_txt = fullfile(struct_txt.folder, struct_txt.name);

% specify scans and multi_regression files
matlabbatch{1}.spm.stats.fmri_spec.sess.scans = cellstr(path_rsub);
matlabbatch{1}.spm.stats.fmri_spec.sess.multi_reg = cellstr(path_txt);

% setup batch job structure
% dir
matlabbatch{1}.spm.stats.fmri_spec.dir = cellstr(path_run); %{path_output};

% timing
matlabbatch{1}.spm.stats.fmri_spec.timing.units = struct_levels.timing_units;
matlabbatch{1}.spm.stats.fmri_spec.timing.RT = struct_levels.timing_RT;

unames = unique(names);

if exist(fullfile(path_run,'SPM.mat'))
  delete(fullfile(path_run,'SPM.mat'));
end

for s = 1:numel(unames)
  name_event = unames{s};
  subOnset = struct_levels.conditionOnset(strcmp(names, unames{s}));
  subDuration = struct_levels.conditionDuration(strcmp(names, unames{s}));


  matlabbatch{1}.spm.stats.fmri_spec.sess.cond(s).name = name_event;
  matlabbatch{1}.spm.stats.fmri_spec.sess.cond(s).onset = subOnset;
  matlabbatch{1}.spm.stats.fmri_spec.sess.cond(s).duration = subDuration;
end
%run batch job
spm_jobman('run',matlabbatch);
clear matlabbatch;
end
