function normalize_contrasts(path_input, list_subjects, list_runs)
  spm('defaults','FMRI');
  spm_jobman('initcfg');

  for r = 1:numel(list_runs)
    for s = 1:numel(list_subjects)
      matlabbatch = {};
      path_tpm = [path_input '-output'];
      con_file = fullfile(path_tpm, list_subjects{s}, list_runs{r}, 'con_0001.nii');
      def_file = fullfile(path_input, list_subjects{s}, 'anat', sprintf('y_%s_T1w.nii', list_subjects{s}));

      matlabbatch{1}.spm.spatial.normalise.write.subj.def = {def_file};
      matlabbatch{1}.spm.spatial.normalise.write.subj.resample = {con_file};
      matlabbatch{1}.spm.spatial.normalise.write.woptions.bb = [-78 -112 -70; 78 76 85];
      matlabbatch{1}.spm.spatial.normalise.write.woptions.vox = [2 2 2];
      matlabbatch{1}.spm.spatial.normalise.write.woptions.interp = 4;

      fprintf('Normalisation : %s - %s\n', list_subjects{s}, list_runs{r});
      spm_jobman('run', matlabbatch);
    end
  end
end