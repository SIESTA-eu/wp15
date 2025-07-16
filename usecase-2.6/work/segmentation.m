function segmentation(path_input)

 	list_files = dir(path_input);
	szFiles = size(list_files);
		
	for f = 3:szFiles(1)
		check_sub = startsWith(list_files(f).name, 'sub');
		check_nifti = endsWith(list_files(f).name, '.nii');
		
		if check_sub == true && check_nifti == true
			path_file = fullfile(path_input, list_files(f).name);
			
			% Channel
			matlabbatch{1}.spm.spatial.preproc.channel.biasreg = 0.001;
			matlabbatch{1}.spm.spatial.preproc.channel.biasfwhm = 60;
			matlabbatch{1}.spm.spatial.preproc.channel.write = [0 1];
			matlabbatch{1}.spm.spatial.preproc.channel.vols = cellstr(path_file);  

			% Warp
			matlabbatch{1}.spm.spatial.preproc.warp.reg = [0 0.001 0.5 0.05 0.2];
			matlabbatch{1}.spm.spatial.preproc.warp.affreg = 'mni';
			matlabbatch{1}.spm.spatial.preproc.warp.fwhm = 0;
			matlabbatch{1}.spm.spatial.preproc.warp.samp = 3;  
      matlabbatch{1}.spm.spatial.preproc.warp.write = [1 1];
    
			% Run
			spm_jobman('run',matlabbatch); 
			clear matlabbatch;
			
		end 
	end
end