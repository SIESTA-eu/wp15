function run_participant(path_input, path_output, participant_id, session_id)

  if nargin<3 || isempty(participant_id)
    participant_id = 'all';
  end

  if nargin<4 || isempty(session_id)
    session_id = 'all';
  end
  
  if isequal(session_id, 'all')
    % replace by the wildcard
    session_id = 'ses*';
  end

  if isequal(participant_id, 'all')
    participants   = readtable(fullfile(path_output, 'participants.tsv'), 'filetype', 'text');
    participant_id = participants.participant_id;
  end

  if ~iscell(participant_id)
    participant_id = {participant_id};
  end
  
  if ~iscell(session_id)
    session_id = {session_id};
  end

  for p = participant_id(:)'
    for s = session_id(:)'
      spm_preprocess(path_output, p{1}, s{1});
      spm_glm(path_output, p{1}, s{1});
    end
  end

end
