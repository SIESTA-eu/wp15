function analyze_participant(inputprefix, outputprefix)

    % This code is shared under the CC0 license
    %
    % Copyright (C) 2024, SIESTA workpackage 15 team

    if ~exist(outputprefix, 'dir')
        mkdir(outputprefix);
    end

    participants = ft_read_tsv(fullfile(inputprefix, 'participants.tsv'));

    % be sure that the emptyroom is not there
    % participants = participants(~isnan(participants.age), :);
    participants = participants(~contains(participants.participant_id, 'emptyroom'), :);    

    nsubj = size(participants,1);
    nruns = 2; % do the computations for the first few runs only

    for subject = 1:nsubj

      close all

      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
      %% use the identifier from the participants file
      subjname = participants.participant_id{subject};

      megfile = cell(1,nruns); % these are the raw data files, they come with the events.tsv
      sssfile = cell(1,nruns); % these are the MaxFiltered data files
      for run=1:nruns
        megfile{run} = fullfile(inputprefix, sprintf('%s/ses-meg/meg/%s_ses-meg_task-facerecognition_run-%02d_meg.fif', subjname, subjname, run));
        sssfile{run} = fullfile(inputprefix, sprintf('derivatives/meg_derivatives/%s/ses-meg/meg/%s_ses-meg_task-facerecognition_run-%02d_proc-sss_meg.fif', subjname, subjname, run));
      end

      mrifile = fullfile(inputprefix, sprintf('%s/ses-mri/anat/%s_ses-mri_acq-mprage_T1w.nii.gz', subjname, subjname));

      coordsystemfile = fullfile(inputprefix, sprintf('%s/ses-meg/meg/%s_ses-meg_coordsystem.json', subjname, subjname));
      coordsystem = ft_read_json(coordsystemfile);

      NAS = coordsystem.AnatomicalLandmarkCoordinates.Nasion;
      LPA = coordsystem.AnatomicalLandmarkCoordinates.LPA;
      RPA = coordsystem.AnatomicalLandmarkCoordinates.RPA;

      outputpath = fullfile(outputprefix, sprintf('%s', subjname));
      mkdir(outputpath);

      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
      %% Reading and preprocessing

      % the data set consists of MEG and EEG
      % furthermore there is anatomical and functional MRI, but that is not considered here

      nruns = length(megfile);
      block = cell(1, nruns);

      % We want to create three categories of events, based on their numerical codes:
      % Famous faces:      5 (00101),  6 (00110),  7 (00111) => Bit 3 only
      % Unfamiliar faces: 13 (01101), 14 (01110), 15 (01111) => Bit 3 and 4
      % Scrambled images: 17 (10001), 18 (10010), 19 (10011) => Bit 5 only

      % the MEG+EEG data is acquired in 6 blocks, each represented in a single file
      for i=1:nruns

        cfg = [];
        % define the trials on basis of the original raw datafile
        % the maxfiltered version does not include the events.tsv
        cfg.dataset = megfile{i};

        cfg.trialfun = 'ft_trialfun_bids';
        cfg.trialdef.eventtype = {'Famous', 'Unfamiliar', 'Scrambled'};
        cfg.trialdef.prestim  = 0.5;
        cfg.trialdef.poststim = 1.2;

        % aligning the MEG time course data with perception and behavior
        cfg = ft_definetrial(cfg);

        % read the maxfiltered version of the raw data
        cfg.dataset = sssfile{i};
        cfg.readbids = 'no';

        % cfg.channel = 'all';
        % cfg.channel = 'megmag';
        % cfg.channel = 'eeg';
        cfg.channel = 'meggrad';
        cfg.baselinewindow = [-inf 0];
        cfg.demean = 'yes';
        cfg.precision = 'single';
        cfg.coilaccuracy = 1;

        % read and preprocess the trials of interest from the data
        block{i} = ft_preprocessing(cfg);
      end

      % show the two different types of trial codes
      disp(block{1}.trialinfo);

      % combine all six blocks into a single
      cfg = [];
      cfg.keepsampleinfo = 'no';
      cfg.outputfile = fullfile(outputpath, 'raw.mat');
      raw = ft_appenddata(cfg, block{:});

      clear block

      %%

      % some downstream analysis may get stuck if it encounters both grad and elec fields
      raw = rmfield(raw, 'elec');

      % FIXME this should be addressed in the fieldtrip code: specifically for me (JM) ft_combineplanar
      % did not run without error, because it did not correctly detect the senstyp automatically

      %% Deal with maxfiltering

      % the data has been maxfiltered and subsequently concatenated
      % this will result in an ill-conditioned estimate of covariance or CSD

      cfg = [];
      cfg.method = 'pca';
      cfg.updatesens = 'no';
      cfg.channel = 'meggrad';
      % cfg.inputfile = fullfile(outputpath, 'raw.mat');
      cfg.outputfile = fullfile(outputpath, 'comp.mat');
      comp = ft_componentanalysis(cfg, raw);

      clear raw

      cfg = [];
      cfg.updatesens = 'no';
      cfg.component = comp.label(51:end);
      % cfg.inputfile = fullfile(outputpath, 'comp.mat');
      cfg.outputfile = fullfile(outputpath, 'raw_subspace.mat');
      raw_subspace = ft_rejectcomponent(cfg, comp);

      clear comp

      cfg = [];
      cfg.baselinewindow = [-inf 0];
      cfg.demean = 'yes';
      cfg.precision = 'single';
      % cfg.inputfile = fullfile(outputpath, 'raw_subspace.mat');
      cfg.outputfile = fullfile(outputpath, 'raw_subspace_demean.mat');
      raw_subspace_demean = ft_preprocessing(cfg, raw_subspace);

      clear raw_subspace


      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
      %% Data reviewing and artifact handling

      cfg = [];
      cfg.metric = 'std';
      cfg.threshold = 10e-12; % pT
      % cfg.inputfile = fullfile(outputpath, 'raw_subspace_demean.mat');
      cfg.outputfile = fullfile(outputpath, 'raw_clean.mat');
      raw_clean = ft_baddata(cfg, raw_subspace_demean);

      clear raw_subspace_demean


      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
      %% Averaging and Event-Related Fields

      cfg = [];
      % cfg.inputfile = fullfile(outputpath, 'raw_clean.mat');

      % in the selection of trials for averaging we prune the timelocked data to an equal number of trials for each of the conditions that is compared
      % this is needed to prevent a bias the the combined planar gradient average and invalid statistical results
      select_faces      = find(strcmp(raw_clean.trialinfo.stim_type, 'Famous') | strcmp(raw_clean.trialinfo.stim_type, 'Unfamiliar'));
      select_scrambled  = find(strcmp(raw_clean.trialinfo.stim_type, 'Scrambled'));
      select_famous     = find(strcmp(raw_clean.trialinfo.stim_type, 'Famous'));
      select_unfamiliar = find(strcmp(raw_clean.trialinfo.stim_type, 'Unfamiliar'));

      % equate the number of trials for the faces versus scrambled comparison
      ntrials = min(length(select_faces), length(select_scrambled));
      select_random = randperm(length(select_faces));
      select_faces = select_faces(select_random(1:ntrials));
      select_random = randperm(length(select_scrambled));
      select_scrambled = select_scrambled(select_random(1:ntrials));

      cfg.trials = select_faces;
      cfg.outputfile = fullfile(outputpath, 'timelock_faces.mat');
      timelock_faces = ft_timelockanalysis(cfg, raw_clean);

      cfg.trials = select_scrambled;
      cfg.outputfile = fullfile(outputpath, 'timelock_scrambled.mat');
      timelock_scrambled = ft_timelockanalysis(cfg, raw_clean);

      % equate the number of trials for the famous versus unfamiliar comparison
      ntrials = min(length(select_famous), length(select_unfamiliar));
      select_random = randperm(length(select_famous));
      select_famous = select_famous(select_random(1:ntrials));
      select_random = randperm(length(select_unfamiliar));
      select_unfamiliar = select_unfamiliar(select_random(1:ntrials));

      cfg.trials = select_famous;
      cfg.outputfile = fullfile(outputpath, 'timelock_famous.mat');
      timelock_famous = ft_timelockanalysis(cfg, raw_clean);

      cfg.trials = select_unfamiliar;
      cfg.outputfile = fullfile(outputpath, 'timelock_unfamiliar.mat');
      timelock_unfamiliar = ft_timelockanalysis(cfg, raw_clean);

      clear raw_clean

      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
      %% Visualization

      cfg = [];
      cfg.layout = 'neuromag306planar';
      ft_multiplotER(cfg, timelock_faces, timelock_scrambled);
      print('-dpng', fullfile(outputpath, 'faces_and_scrambled.png'));
      ft_multiplotER(cfg, timelock_famous, timelock_unfamiliar);
      print('-dpng', fullfile(outputpath, 'famous_and_unfamiliar.png'));

      cfg = [];
      timelock_faces_cmb       = ft_combineplanar(cfg, timelock_faces);
      timelock_scrambled_cmb   = ft_combineplanar(cfg, timelock_scrambled);
      timelock_famous_cmb      = ft_combineplanar(cfg, timelock_famous);
      timelock_unfamiliar_cmb  = ft_combineplanar(cfg, timelock_unfamiliar);

      cfg = [];
      cfg.layout = 'neuromag306cmb';
      ft_multiplotER(cfg, timelock_faces_cmb, timelock_scrambled_cmb);
      print('-dpng', fullfile(outputpath, 'faces_cmb_and_scrambled_cmb.png'));
      ft_multiplotER(cfg, timelock_famous_cmb, timelock_unfamiliar_cmb);
      print('-dpng', fullfile(outputpath, 'famous_cmb_and_unfamiliar_cmb.png'));


      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
      %% Visualization of contrasts

      cfg = [];
      cfg.parameter = 'avg';
      cfg.operation = 'x1-x2';
      faces_vs_scrambled_diff   = ft_math(cfg, timelock_faces, timelock_scrambled);
      famous_vs_unfamiliar_diff = ft_math(cfg, timelock_famous, timelock_unfamiliar);

      % note that these are the combined planar gradient representations of the difference
      % not the differences of the combined planar gradient representations
      cfg = [];
      faces_vs_scrambled_diff_cmb   = ft_combineplanar(cfg, faces_vs_scrambled_diff);
      famous_vs_unfamiliar_diff_cmb = ft_combineplanar(cfg, famous_vs_unfamiliar_diff);

      cfg = [];
      cfg.layout = 'neuromag306cmb';

      figure
      ft_multiplotER(cfg, faces_vs_scrambled_diff_cmb);
      print('-dpng', fullfile(outputpath, 'faces_vs_scrambled_diff_cmb.png'));

      figure
      ft_multiplotER(cfg, famous_vs_unfamiliar_diff_cmb);
      print('-dpng', fullfile(outputpath, 'famous_vs_unfamiliar_diff_cmb.png'));

    end % for each subject
