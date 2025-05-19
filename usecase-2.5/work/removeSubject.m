function removeSubject(path_input)
	list_fmris = dir(path_input);
	szFMRIs = size(list_fmris);
	
	for m = 3:szFMRIs(1)
		path_fmri = fullfile(path_input, list_fmris(m).name);
		check_folder = isfolder(path_fmri);
		
		if check_folder == false
			delete(path_fmri);
		end 
		
		if check_folder == true
			list_files = dir(path_fmri);
			szFiles = size(list_files);
			
			for f = 3:szFiles(1)
				path_file = fullfile(path_fmri, list_files(f).name);
				delete(path_file);
			end 
			rmdir(path_fmri);
		end 
	end
	rmdir(path_input);
end
	