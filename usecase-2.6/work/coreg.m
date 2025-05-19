function coreg(path_source, path_func, path_output)
    			
	listFunc_files = dir(path_func);
	szFunc = size(listFunc_files);
	
	for f = 3:szFunc(1)
		check_mean = startsWith(listFunc_files(f).name, "mean");
				
		if check_mean == true 
			path_ref = fullfile(path_func, listFunc_files(f).name);
													
			% Ref
			matlabbatch{1}.spm.spatial.coreg.estimate.ref = cellstr(path_ref);
        
			% Source
			matlabbatch{1}.spm.spatial.coreg.estimate.source = cellstr(path_source);
        
			% Eoptions
			matlabbatch{1}.spm.spatial.coreg.estimate.eoptions.cost_fun = 'nmi';
			matlabbatch{1}.spm.spatial.coreg.estimate.eoptions.sep = [4 2];
			matlabbatch{1}.spm.spatial.coreg.estimate.eoptions.tol = [0.02 0.02 0.02 0.001 0.001 0.001 0.01 0.01 0.01 0.001 0.001 0.001];
			matlabbatch{1}.spm.spatial.coreg.estimate.eoptions.fwhm = [7 7];
        
			% Run
			spm_jobman('run',matlabbatch);    
			clear matlabbatch;
		end 
	end

	list_files = dir(path_func);
	szFiles = size(list_files);

	for f = 3:szFiles(1)
		check_rp = startsWith(list_files(f).name, 'rp_');
		check_mat = endsWith(list_files(f).name, '.mat');
		check_mean = startsWith(list_files(f).name, 'mean');
		check_rsub = startsWith(list_files(f).name, 'rsub');

		if check_mat == true
			path_mat = fullfile(path_func, list_files(f).name);
			event = extractEvents(list_files(f).name);
			path_event = fullfile(path_output, event);
      if ~exist(path_event, 'dir')
        mkdir(path_event);
      end
			copyfile(path_mat, path_event);
			delete(path_mat);
		end 
		
		if check_rp == true 
			path_rp = fullfile(path_func, list_files(f).name);
			event = extractEvents(list_files(f).name);
			path_event = fullfile(path_output, event);
      if ~exist(path_event, 'dir')
        mkdir(path_event);
      end
			copyfile(path_rp, path_event);
			delete(path_rp);
		end 

		if check_mean == true
			path_mean = fullfile(path_func, list_files(f).name);
			event = extractEvents(list_files(f).name);
			path_event = fullfile(path_output, event);
      if ~exist(path_event, 'dir')
        mkdir(path_event);
      end
			copyfile(path_mean, path_event);
			delete(path_mean);
		end

		if check_rsub == true
			path_rfile = fullfile(path_func, list_files(f).name);
			event = extractEvents(list_files(f).name);
			path_event = fullfile(path_output, event);
      if ~exist(path_event, 'dir')
        mkdir(path_event);
      end
			copyfile(path_rfile, path_event);
			delete(path_rfile);
		end
	end
end
