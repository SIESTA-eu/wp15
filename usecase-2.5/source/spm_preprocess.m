function structPreProcess = spm_preprocess(path_input)
	
	path_source = '';
	path_anat = fullfile(path_input, 'anat');
	list_files = dir(path_anat);
	szFiles = size(list_files);

	for f = 3:szFiles(1)
		path_file = fullfile(path_anat, list_files(f).name);
		check_nifti = endsWith(list_files(f).name, '.nii');
		
		if check_nifti == true
			path_source = path_file;
			%disp('Step 1 -- Segmentation and Normalization');
			%segmentation(path_anat);
			%disp('Step 1 - done!');	
		end
	end

	list_fmris = dir(path_input);
	szFMRIs = size(list_fmris);	

	for m = 3:szFMRIs(1)
		path_fmri = fullfile(path_input, list_fmris(m).name);
		check_fmri = isfolder(path_fmri);			
		structPreProcess = struct;

		if check_fmri == true		
			disp('Step 2 -- Realign all volumes to first functional volume');
			realign(path_fmri);
			disp('Step 2 - Done!');
		end 
								
		list_files = dir(path_fmri);
		szFiles = size(list_files);
				
		path_func = fullfile(path_input, 'func');
		
		disp('Step 3 -- Coregister structural image to first dynamic image');
		coreg(path_source, path_func);
		disp('Step 3 - Done!'); 
									
		disp('Step 4 -- Gaussian kernel smoothing of realigned data');
		smooth(path_anat);
		disp('Step 4 is done !');
     end
end
