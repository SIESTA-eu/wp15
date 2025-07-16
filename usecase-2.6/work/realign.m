function realign(path_input) 
	
	list_files = dir(fullfile(path_input, 'sub*nii'));
	szFiles = size(list_files);
	
	for f = 1:szFiles(1)
    	check_nifti = endsWith(list_files(f).name, '.nii');
	
		if check_nifti == true
      		path_file = fullfile(path_input, list_files(f).name);  
			
			V = spm_vol(path_file);
			Vsize = size(V);
			Nt = Vsize(1);
			fnms={};
            
			for i = 1:Nt
				fnms{i} = [path_file ',' num2str(i) ];
			end
        
			%Data
			matlabbatch{1}.spm.spatial.realign.estwrite.data={fnms'};
			matlabbatch{1}.spm.temporal.st.nslices = 38;
			matlabbatch{1}.spm.temporal.st.tr = 2;
			matlabbatch{1}.spm.temporal.st.ta = 1.94736842105263;
			matlabbatch{1}.spm.temporal.st.refslice = 19;
			matlabbatch{1}.spm.temporal.st.prefix = 'a';
            
			% Eoptions
			matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.quality = 0.9;
			matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.sep = 4;
			matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.fwhm = 5;
			matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.rtm = 1;
			matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.interp = 2;
			matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.wrap = [0 0 0];
			matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.weight = '';
            
			%Roptions
			matlabbatch{1}.spm.spatial.realign.estwrite.roptions.which = [2 1];
			matlabbatch{1}.spm.spatial.realign.estwrite.roptions.interp = 4;
			matlabbatch{1}.spm.spatial.realign.estwrite.roptions.wrap = [0 0 0];
			matlabbatch{1}.spm.spatial.realign.estwrite.roptions.mask = 1;
			matlabbatch{1}.spm.spatial.realign.estwrite.roptions.prefix = 'r'; 
            
			% Run
			spm_jobman('run', matlabbatch);   
		end
	end		
end