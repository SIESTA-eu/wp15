outputprefix = fullfile(pwd, 'output');
mkdir(fullfile(outputprefix, 'group'));

warning off

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% load the single subject averages
timelock_famous     = {};
timelock_unfamiliar = {};
timelock_scrambled  = {};
timelock_faces      = {};

for subject=1:16
  subjectpath = fullfile(outputprefix, sprintf('sub-%02d', subject));
  
  tmp = load(fullfile(subjectpath, 'timelock_famous'));
  timelock_famous{subject} = tmp.timelock;
  
  tmp = load(fullfile(subjectpath, 'timelock_unfamiliar'));
  timelock_unfamiliar{subject} = tmp.timelock;
  
  tmp = load(fullfile(subjectpath, 'timelock_scrambled'));
  timelock_scrambled{subject} = tmp.timelock;
  
  tmp = load(fullfile(subjectpath, 'timelock_faces'));
  timelock_faces{subject} = tmp.timelock;
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% compute planar gradients

timelock_famous_cmb     = {};
timelock_unfamiliar_cmb = {};
timelock_scrambled_cmb  = {};
timelock_faces_cmb      = {};

for i=1:16
  disp(i)
  cfg = [];
  timelock_famous_cmb{i}     = ft_combineplanar(cfg, timelock_famous{i});
  timelock_unfamiliar_cmb{i} = ft_combineplanar(cfg, timelock_unfamiliar{i});
  timelock_scrambled_cmb{i}  = ft_combineplanar(cfg, timelock_scrambled{i});
  timelock_faces_cmb{i}      = ft_combineplanar(cfg, timelock_faces{i});
end

% this is a bit of a lengthy step, hence save the intermediate results
save(fullfile(outputprefix, 'group', 'timelock_famous_cmb'), 'timelock_famous_cmb');
save(fullfile(outputprefix, 'group', 'timelock_unfamiliar_cmb'), 'timelock_unfamiliar_cmb');
save(fullfile(outputprefix, 'group', 'timelock_scrambled_cmb'), 'timelock_scrambled_cmb');
save(fullfile(outputprefix, 'group', 'timelock_faces_cmb'), 'timelock_faces_cmb');

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% compute grand averages

timelock_famous_cmb_ga     = ft_timelockgrandaverage(cfg, timelock_famous_cmb{:});
timelock_unfamiliar_cmb_ga = ft_timelockgrandaverage(cfg, timelock_unfamiliar_cmb{:});
timelock_scrambled_cmb_ga  = ft_timelockgrandaverage(cfg, timelock_scrambled_cmb{:});
timelock_faces_cmb_ga      = ft_timelockgrandaverage(cfg, timelock_faces_cmb{:});

%% visualise the grand-averages

cfg = [];
cfg.layout = 'neuromag306cmb';
figure
ft_multiplotER(cfg, timelock_faces_cmb_ga, timelock_scrambled_cmb_ga);
figure
ft_multiplotER(cfg, timelock_famous_cmb_ga, timelock_unfamiliar_cmb_ga);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% do standard statistical comparison between conditions

cfg = [];
cfg.method = 'analytic';
cfg.statistic = 'depsamplesT';
cfg.correctm = 'fdr';
cfg.design = [
  1:16          1:16
  1*ones(1,16)  2*ones(1,16)
  ];
cfg.uvar = 1; % unit of observation, i.e. subject
cfg.ivar = 2; % independent variable, i.e. stimulus

stat_cmb_faces_vs_scrambled   = ft_timelockstatistics(cfg, timelock_faces_cmb{:},  timelock_scrambled_cmb{:});
stat_cmb_famous_vs_unfamiliar = ft_timelockstatistics(cfg, timelock_famous_cmb{:}, timelock_unfamiliar_cmb{:});

% this is a bit of a lengthy step, hence save the results
save(fullfile(outputprefix, 'group', 'stat_cmb_faces_vs_scrambled'), 'stat_cmb_faces_vs_scrambled');
save(fullfile(outputprefix, 'group', 'stat_cmb_famous_vs_unfamiliar'), 'stat_cmb_famous_vs_unfamiliar');

% quick and dirty visualisation
figure;
subplot(2,1,1)
h = imagesc(-log10(stat_cmb_faces_vs_scrambled.prob)); colorbar
subplot(2,1,2)
h = imagesc(-log10(stat_cmb_faces_vs_scrambled.prob)); colorbar
set(h, 'AlphaData', stat_cmb_faces_vs_scrambled.mask);
print('-dpng', fullfile(outputprefix, 'group', 'stat_cmb_faces_vs_scrambled.png'));


%% compute the condition difference
cfg = [];
cfg.parameter = 'avg';
cfg.operation = 'x1-x2';
diff_cmb_faces_vs_scrambled = ft_math(cfg, timelock_faces_cmb_ga, timelock_scrambled_cmb_ga);
diff_cmb_famous_vs_unfamiliar = ft_math(cfg, timelock_famous_cmb_ga, timelock_unfamiliar_cmb_ga);

% save the results
save(fullfile(outputprefix, 'group', 'diff_cmb_faces_vs_scrambled'), 'diff_cmb_faces_vs_scrambled');
save(fullfile(outputprefix, 'group', 'diff_cmb_famous_vs_unfamiliar'), 'diff_cmb_famous_vs_unfamiliar');

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% more detailed visualisation

% add the statistical mask to the data
diff_cmb_faces_vs_scrambled.mask = stat_cmb_faces_vs_scrambled.mask;
diff_cmb_famous_vs_unfamiliar.mask = stat_cmb_famous_vs_unfamiliar.mask;

cfg = [];
cfg.layout = 'neuromag306cmb';
cfg.parameter = 'avg';
cfg.maskparameter = 'mask';
figure
ft_multiplotER(cfg, diff_cmb_faces_vs_scrambled);
print('-dpng', fullfile(outputprefix, 'group', 'diff_cmb_faces_vs_scrambled_stat.png'));

figure
ft_multiplotER(cfg, diff_cmb_famous_vs_unfamiliar);
print('-dpng', fullfile(outputprefix, 'group', 'diff_cmb_famous_vs_unfamiliar_stat.png'));

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% determine the neighbours that we consider to share evidence in favour of H1

cfg = [];
cfg.layout = 'neuromag306cmb';
cfg.method = 'distance';
cfg.neighbourdist = 0.15;
cfg.feedback = 'yes';
neighbours_cmb = ft_prepare_neighbours(cfg); % this is an example of a poor neighbourhood definition

print('-dpng', fullfile(outputprefix, 'group', 'neighbours_cmb_distance.png'));

cfg.layout = 'neuromag306cmb';
cfg.method = 'triangulation';
cfg.feedback = 'yes';
neighbours_cmb = ft_prepare_neighbours(cfg); % this one is better, but could use some manual adjustments

print('-dpng', fullfile(outputprefix, 'group', 'neighbours_cmb_triangulation.png'));

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% do a more sensitive channel-level statistical analysis

cfg = [];
cfg.method = 'montecarlo';
cfg.numrandomization = 500;
cfg.statistic = 'depsamplesT';
cfg.correctm = 'cluster';
cfg.neighbours = neighbours_cmb;
cfg.design = [
  1:16          1:16
  1*ones(1,16)  2*ones(1,16)
  ];
cfg.uvar = 1; % unit of observation, i.e. subject
cfg.ivar = 2; % independent variable, i.e. stimulus

cluster_cmb_faces_vs_scrambled   = ft_timelockstatistics(cfg, timelock_faces_cmb{:},  timelock_scrambled_cmb{:});
cluster_cmb_famous_vs_unfamiliar = ft_timelockstatistics(cfg, timelock_famous_cmb{:}, timelock_unfamiliar_cmb{:});

% this is a very lengthy step, hence save the results
save(fullfile(outputprefix, 'group', 'cluster_cmb_faces_vs_scrambled'), 'cluster_cmb_faces_vs_scrambled');
save(fullfile(outputprefix, 'group', 'cluster_cmb_famous_vs_unfamiliar'), 'cluster_cmb_famous_vs_unfamiliar');

%% visualisation

% add the statistical mask to the data
diff_cmb_faces_vs_scrambled_.mask = cluster_cmb_faces_vs_scrambled.mask;
diff_cmb_famous_vs_unfamiliar.mask = cluster_cmb_famous_vs_unfamiliar.mask;

cfg = [];
cfg.layout = 'neuromag306cmb';
cfg.parameter = 'avg';
cfg.maskparameter = 'mask';
figure
ft_multiplotER(cfg, diff_cmb_faces_vs_scrambled);
print('-dpng', fullfile(outputprefix, 'group', 'diff_cmb_faces_vs_scrambled_cluster.png'));

figure
ft_multiplotER(cfg, diff_cmb_famous_vs_unfamiliar);
print('-dpng', fullfile(outputprefix, 'group', 'diff_cmb_famous_vs_unfamiliar.png'));


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% show full provenance of the final analysis

cfg = [];
cfg.filetype = 'html';
cfg.filename = fullfile(outputprefix, 'group', 'cluster_cmb_faces_vs_scrambled');
ft_analysispipeline(cfg, cluster_cmb_faces_vs_scrambled);

