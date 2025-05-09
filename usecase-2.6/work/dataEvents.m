% retrieve data onset and duration written in tsv files located at path_input
function output = dataEvents(path_file, info) 
	
	output = [''];

	%arrayOnset = zeros(1,1);
	%arrayDuration = zeros(1,1);
					
	T = readtable(path_file, 'filetype', 'text', 'delimiter', '\t');
	onset = T.onset;
	duration = T.duration;
	trial = T.trial_type;
	szOnset = size(onset);
	c = categorical(trial);
	events = categories(c);
	countEvents = countcats(c);
	sz = size(events);

	check_name = strcmp(info, 'event');

	if check_name == true
		for e = 1:sz(1)
			tmp_event = events{e};
			sz_event = size(tmp_event);
			trial_type = '';
			for s = 1:sz_event(2)
				trial_type = append(trial_type, tmp_event(s));
			end
			output = trial_type;
		end
	end
	
	if check_name == false
		Onset = [];
		index_onset = 1;
		Duration = [];
		index_duration = 1;
		check_onset = strcmp(info, 'onset');
		check_duration = strcmp(info, 'duration');

		for e = 1:sz(1)
			name = events(e);
			rows = countEvents(e);
			Duration = [];
			index_duration = 1;
			for r = 1:szOnset(1)
				check_word = strcmp(name, trial(r));
					
				if check_onset == true && check_word == true
					Onset(index_onset) = onset(r);
					index_onset = index_onset + 1;
				end 

				if check_duration == true && check_word == true
					Duration(index_duration) = duration(r);
					index_duration = index_duration + 1;
			end				
		end

		if check_onset == true
			output = Onset;
		end

		if check_duration == true
			output = Duration;
		end
	end
end 