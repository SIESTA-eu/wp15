% apply some contrasts to SPM.mat file  
function contrasts(path_output)

	split_output = strsplit(path_output, '/');
	directory_name = split_output{end};

	disp(path_output);
	disp(directory_name);
	
	check_dots = startsWith(directory_name, 'DOTS');
	check_motion = startsWith(directory_name, 'Motion');
	check_spwm = startsWith(directory_name, 'spWM');

	%list_runs = dir(path_output);
	%szRuns = size(list_runs);
	
	path_spmmat = fullfile(path_output, 'SPM.mat');

	SPM_loaded = load(path_spmmat);
	disp('Nombre de régressors dans le modèle :');
	disp(size(SPM_loaded.SPM.xX.X, 2));

	matlabbatch{1}.spm.stats.con.spmmat = cellstr(path_spmmat);
	%Reproduce across sessions: 'none' dont replicate; 'sess' create per session; 'repl' replicate; 'both' replicate and create
			
	% dots et Motion
	if check_dots == true || check_motion == true
		matlabbatch{1}.spm.stats.con.consess{1}.tcon.name = 'contrast';         % t Contrast
		matlabbatch{1}.spm.stats.con.consess{1}.tcon.weights = [-1 0 0 1]; %[0 0 0 1] 
		matlabbatch{1}.spm.stats.con.consess{1}.tcon.sessrep = 'none'; 
	end 

	if check_spwm == true 
		matlabbatch{1}.spm.stats.con.consess{1}.tcon.name = 'contrast';         % t Contrast
		matlabbatch{1}.spm.stats.con.consess{1}.tcon.weights = [1 0 0 0]; %[0 0 0 1]
		matlabbatch{1}.spm.stats.con.consess{1}.tcon.sessrep = 'none'; 
	end 

	spm_jobman('run', matlabbatch);
end
