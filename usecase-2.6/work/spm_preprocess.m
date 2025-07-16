function spm_preprocess(path_input, path_output)

  addpath('/work')

  path_source = '';
  path_anat = fullfile(path_input, 'anat');
  unzipMRIs(path_anat);

  path_func = fullfile(path_input, 'func');
  unzipMRIs(path_func);

  list_files = dir(path_anat);
  szFiles = size(list_files);

  for f = 3:szFiles(1)
    path_file = fullfile(path_anat, list_files(f).name);
    check_nifti = endsWith(list_files(f).name, '.nii');

    if check_nifti == true
      path_source = path_file;
    end
  end

  list_fmris = dir(path_input);
  szFMRIs = size(list_fmris);

  for m = 3:szFMRIs(1)
    path_fmri = fullfile(path_input, list_fmris(m).name);
    check_fmri = isfolder(path_fmri);

    if check_fmri == true
      disp('Step 2 -- Realign all volumes to first functional volume');
      realign(path_fmri);
      disp('Step 2 - Done!');
    end
  end

  disp('Step 3 -- Coregister structural image to first dynamic image');
  coreg(path_source, path_func, path_output);
  disp('Step 3 - Done!');

  disp('Step 4 -- Gaussian kernel smoothing of realigned data');
  segmentation(path_anat);
  disp('Step 4 is done !');
end
