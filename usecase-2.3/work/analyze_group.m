function analyze_group(inputprefix, outputprefix)

    % This code is shared under the CC0 license
    %
    % Copyright (C) 2024, SIESTA workpackage 15 team
  
    if ~exist(outputprefix, 'dir')
        mkdir(outputprefix);
    end

    grouppath = fullfile(outputprefix, 'group');
    mkdir(grouppath);

    warning off

    participants = ft_read_tsv(fullfile(inputprefix, 'participants.tsv'));

    % be sure that the emptyroom is not there
    participants = participants(~contains(participants.participant_id, 'emptyroom'), :);    
    nsubj = size(participants,1);


    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %% load the single subject averages
    timelock_faces      = cell(1,nsubj);
    timelock_scrambled  = cell(1,nsubj);
    timelock_famous     = cell(1,nsubj);
    timelock_unfamiliar = cell(1,nsubj);

    for subject=1:nsubj
      % use the identifier from the participants file
      subjname = participants.participant_id{subject};

      subjectpath = fullfile(outputprefix, sprintf('%s', subjname));

      tmp = load(fullfile(subjectpath, 'timelock_faces'));
      timelock_faces{subject} = tmp.timelock;

      tmp = load(fullfile(subjectpath, 'timelock_scrambled'));
      timelock_scrambled{subject} = tmp.timelock;

      tmp = load(fullfile(subjectpath, 'timelock_famous'));
      timelock_famous{subject} = tmp.timelock;

      tmp = load(fullfile(subjectpath, 'timelock_unfamiliar'));
      timelock_unfamiliar{subject} = tmp.timelock;
    end


    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %% compute single-subject planar gradients

    timelock_faces_cmb      = cell(1,nsubj);
    timelock_scrambled_cmb  = cell(1,nsubj);
    timelock_famous_cmb     = cell(1,nsubj);
    timelock_unfamiliar_cmb = cell(1,nsubj);

    for i=1:nsubj
      disp(i)
      cfg = [];
      timelock_faces_cmb{i}      = ft_combineplanar(cfg, timelock_faces{i});
      timelock_scrambled_cmb{i}  = ft_combineplanar(cfg, timelock_scrambled{i});
      timelock_famous_cmb{i}     = ft_combineplanar(cfg, timelock_famous{i});
      timelock_unfamiliar_cmb{i} = ft_combineplanar(cfg, timelock_unfamiliar{i});
    end


    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %% compute and visualise the grand-averages

    cfg = [];
    timelock_faces_cmb_ga      = ft_timelockgrandaverage(cfg, timelock_faces_cmb{:});
    timelock_scrambled_cmb_ga  = ft_timelockgrandaverage(cfg, timelock_scrambled_cmb{:});
    timelock_famous_cmb_ga     = ft_timelockgrandaverage(cfg, timelock_famous_cmb{:});
    timelock_unfamiliar_cmb_ga = ft_timelockgrandaverage(cfg, timelock_unfamiliar_cmb{:});

    save(fullfile(grouppath, 'timelock_faces_cmb_ga'), 'timelock_faces_cmb_ga');
    save(fullfile(grouppath, 'timelock_scrambled_cmb_ga'), 'timelock_scrambled_cmb_ga');
    save(fullfile(grouppath, 'timelock_famous_cmb_ga'), 'timelock_famous_cmb_ga');
    save(fullfile(grouppath, 'timelock_unfamiliar_cmb_ga'), 'timelock_unfamiliar_cmb_ga');

    cfg = [];
    cfg.layout = 'neuromag306cmb';
    cfg.ylim = 'zeromax';
    figure
    ft_multiplotER(cfg, timelock_faces_cmb_ga, timelock_scrambled_cmb_ga);
    print('-dpng', fullfile(grouppath, 'faces_cmb_and_scrambled_cmb.png'));

    figure
    ft_multiplotER(cfg, timelock_famous_cmb_ga, timelock_unfamiliar_cmb_ga);
    print('-dpng', fullfile(grouppath, 'famous_cmb_and_unfamiliar_cmb.png'));

    %% compute and visualise the grand-average condition differences

    % note that these are the differences of the combined planar gradient representations
    % not the combined planar gradient representations of the difference

    cfg = [];
    cfg.parameter = 'avg';
    cfg.operation = 'x1-x2';
    faces_cmb_vs_scrambled_cmb_diff = ft_math(cfg, timelock_faces_cmb_ga, timelock_scrambled_cmb_ga);
    famous_cmb_vs_unfamiliar_cmb_diff = ft_math(cfg, timelock_famous_cmb_ga, timelock_unfamiliar_cmb_ga);

    % save the condition differences
    save(fullfile(grouppath, 'faces_cmb_vs_scrambled_cmb_diff'), 'faces_cmb_vs_scrambled_cmb_diff');
    save(fullfile(grouppath, 'famous_cmb_vs_unfamiliar_cmb_diff'), 'famous_cmb_vs_unfamiliar_cmb_diff');

    cfg = [];
    cfg.layout = 'neuromag306cmb';
    figure
    ft_multiplotER(cfg, faces_cmb_vs_scrambled_cmb_diff);
    print('-dpng', fullfile(grouppath, 'faces_cmb_vs_scrambled_cmb_diff.png'));

    figure
    ft_multiplotER(cfg, famous_cmb_vs_unfamiliar_cmb_diff);
    print('-dpng', fullfile(grouppath, 'famous_cmb_vs_unfamiliar_cmb_diff.png'));


    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %% do standard statistical comparison between conditions

    cfg = [];
    cfg.method = 'analytic';
    cfg.statistic = 'depsamplesT';
    cfg.correctm = 'fdr';
    cfg.design = [
      1:nsubj          1:nsubj
      1*ones(1,nsubj)  2*ones(1,nsubj)
      ];
    cfg.uvar = 1; % unit of observation, i.e. subject
    cfg.ivar = 2; % independent variable, i.e. stimulus

    faces_cmb_vs_scrambled_cmb_fdrstat   = ft_timelockstatistics(cfg, timelock_faces_cmb{:},  timelock_scrambled_cmb{:});
    famous_cmb_vs_unfamiliar_cmb_fdrstat = ft_timelockstatistics(cfg, timelock_famous_cmb{:}, timelock_unfamiliar_cmb{:});

    save(fullfile(grouppath, 'faces_cmb_vs_scrambled_cmb_fdrstat'), 'faces_cmb_vs_scrambled_cmb_fdrstat');
    save(fullfile(grouppath, 'famous_cmb_vs_unfamiliar_cmb_fdrstat'), 'famous_cmb_vs_unfamiliar_cmb_fdrstat');

    %% quick and dirty visualisation

    figure
    subplot(2,1,1)
    h = imagesc(-log10(faces_cmb_vs_scrambled_cmb_fdrstat.prob)); colorbar
    subplot(2,1,2)
    h = imagesc(-log10(faces_cmb_vs_scrambled_cmb_fdrstat.prob)); colorbar
    set(h, 'AlphaData', faces_cmb_vs_scrambled_cmb_fdrstat.mask);
    print('-dpng', fullfile(grouppath, 'faces_cmb_vs_scrambled_cmb_fdrstat.png'));


    %% more detailed visualisation

    % add the statistical mask to the grand-average difference ERF
    faces_cmb_vs_scrambled_cmb_diff.mask = faces_cmb_vs_scrambled_cmb_fdrstat.mask;
    famous_cmb_vs_unfamiliar_cmb_diff.mask = famous_cmb_vs_unfamiliar_cmb_fdrstat.mask;

    cfg = [];
    cfg.layout = 'neuromag306cmb';
    cfg.parameter = 'avg';
    cfg.maskparameter = 'mask';
    figure
    ft_multiplotER(cfg, faces_cmb_vs_scrambled_cmb_diff);
    print('-dpng', fullfile(grouppath, 'faces_cmb_vs_scrambled_cmb_diff.png'));

    figure
    ft_multiplotER(cfg, famous_cmb_vs_unfamiliar_cmb_diff);
    print('-dpng', fullfile(grouppath, 'famous_cmb_vs_unfamiliar_cmb_diff.png'));


    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %% determine the neighbours that we consider to share evidence in favour of H1

    cfg = [];
    cfg.layout = 'neuromag306cmb';
    cfg.method = 'distance';
    cfg.neighbourdist = 0.15;
    cfg.feedback = 'yes';
    neighbours_distance = ft_prepare_neighbours(cfg); % this is an example of a poor neighbourhood definition

    print('-dpng', fullfile(grouppath, 'neighbours_distance.png'));

    cfg.layout = 'neuromag306cmb';
    cfg.method = 'triangulation';
    cfg.feedback = 'yes';
    neighbours_triangulation = ft_prepare_neighbours(cfg); % this one is better, but could use some manual adjustments

    print('-dpng', fullfile(grouppath, 'neighbours_triangulation.png'));


    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %% do a more sensitive cluster-based statistical analysis

    cfg = [];
    cfg.method = 'montecarlo';
    cfg.numrandomization = 500;
    cfg.statistic = 'depsamplesT';
    cfg.correctm = 'cluster';
    cfg.neighbours = neighbours_triangulation;
    cfg.design = [
      1:nsubj          1:nsubj
      1*ones(1,nsubj)  2*ones(1,nsubj)
      ];
    cfg.uvar = 1; % unit of observation, i.e. subject
    cfg.ivar = 2; % independent variable, i.e. stimulus

    faces_cmb_vs_scrambled_cmb_clusterstat   = ft_timelockstatistics(cfg, timelock_faces_cmb{:},  timelock_scrambled_cmb{:});
    famous_cmb_vs_unfamiliar_cmb_clusterstat = ft_timelockstatistics(cfg, timelock_famous_cmb{:}, timelock_unfamiliar_cmb{:});

    % this is a very lengthy step, hence save the results
    save(fullfile(grouppath, 'faces_cmb_vs_scrambled_cmb_clusterstat'), 'faces_cmb_vs_scrambled_cmb_clusterstat');
    save(fullfile(grouppath, 'famous_cmb_vs_unfamiliar_cmb_clusterstat'), 'famous_cmb_vs_unfamiliar_cmb_clusterstat');

    %% quick and dirty visualisation

    figure
    subplot(2,1,1)
    h = imagesc(-log10(faces_cmb_vs_scrambled_cmb_clusterstat.prob)); colorbar
    subplot(2,1,2)
    h = imagesc(-log10(faces_cmb_vs_scrambled_cmb_clusterstat.prob)); colorbar
    set(h, 'AlphaData', faces_cmb_vs_scrambled_cmb_clusterstat.mask);
    print('-dpng', fullfile(grouppath, 'faces_cmb_vs_scrambled_cmb_clusterstat.png'));

    %% more detailed visualisation

    % add the statistical mask to the grand-average difference ERF
    faces_cmb_vs_scrambled_cmb_diff.mask   = faces_cmb_vs_scrambled_cmb_clusterstat.mask;
    famous_cmb_vs_unfamiliar_cmb_diff.mask = famous_cmb_vs_unfamiliar_cmb_clusterstat.mask;

    cfg = [];
    cfg.layout = 'neuromag306cmb';
    cfg.parameter = 'avg';
    cfg.maskparameter = 'mask';
    figure
    ft_multiplotER(cfg, faces_cmb_vs_scrambled_cmb_diff);
    print('-dpng', fullfile(grouppath, 'faces_cmb_vs_scrambled_cmb_diff.png'));

    figure
    ft_multiplotER(cfg, famous_cmb_vs_unfamiliar_cmb_diff);
    print('-dpng', fullfile(grouppath, 'famous_cmb_vs_unfamiliar_cmb_diff.png'));


    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %% show full provenance of the final analysis

    cfg = [];
    cfg.filetype = 'html';
    cfg.filename = fullfile(grouppath, 'faces_cmb_vs_scrambled_cmb_clusterstat');
    ft_analysispipeline(cfg, faces_cmb_vs_scrambled_cmb_clusterstat);

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %% get the average timecourse from the 10 "most significant" channels
    %% in the famous versus unfamiliar contrast

    masksum = sum(famous_cmb_vs_unfamiliar_cmb_diff.mask,2);
    [count, index] = sort(masksum, 'descend');

    % take the 10 channels with largest number of significant timepoints
    chansel = index(1:10);
    % start from the end to not mess up the order when removing elements
    for i = 10:-1:1
      % remove channels that have no significant timepoints
      % this is unlikely, but could happen
      if count(i)<1
        chansel(i) = [];
      end
    end
    if ~isempty(chansel)
      avgsel = mean(famous_cmb_vs_unfamiliar_cmb_diff.avg(chansel,:),1);
    else
      avgsel = nan(size(famous_cmb_vs_unfamiliar_cmb_diff.time));
    end

    result = table(1000*famous_cmb_vs_unfamiliar_cmb_diff.time', 1e15*avgsel', 'VariableNames', {'time (ms)', 'field (fT)'});

    figure; plot(result{:,1}, result{:,2})
    xlabel(result.Properties.VariableNames{1})
    ylabel(result.Properties.VariableNames{2})

    writetable(result, fullfile(grouppath,'results.tsv'), 'FileType','text', Delimiter='\t')
