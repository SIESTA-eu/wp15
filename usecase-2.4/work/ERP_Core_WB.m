function out = ERP_Core_WB(InputDataset,OutputLocation,AnalysisLevel,varargin)

% ERP Core - Whole Brain analysis
% Matlab function calling the EEGLAB toolbox and LIMO MEEG (master from
% Github)
%
% FORMAT ERP_Core_WB(InputDataset,OutputLocation,AnalysisLevel,options)
%        This follows the BIDS App approach to specifying arguments
%
% INPUTS  - InputDataset is the folder where the ERPCore data are located
%           (for AnalysisLevel 1) or where the 1st AnalysisLevel results are located (for
%           AnalysisLevel 2)
%         - OutputLocation is the folder where all results are saved
%           if empty, results are saved in InputDataset/derivatives
%         - AnalysisLevel describes the analysis AnalysisLevel, either '1' for each subject
%           preprocessing and 1st AnalysisLevel GLM, or '2' for the group AnalysisLevel
%           analysis using beta parameters and contrasts from the 1st AnalysisLevel
%         - options as key-value pairs (or a matlab structure with fields as keys)
%         'TaskLabel',{'name1,'name2'} is a cell-array with TaskLabel name to analyze
%                (by default it is {'ERN','MMN','N170','N2pc','N400','P3'})
%         'SubjectLabel',{'sub-001','sub-002','sub-003','sub-005','sub-006','sub-009'}
%                  is a cell-array with subject identifiers to run for a subset of subjects only
%                  (at least 6 subjects to run the paired t-test)
%          other arguments are EEGLAB/LIMO specifics for AnalysisLevel 1
%          high_pass - filter value (0.5Hz default) in pop_clean_rawdataset as [value-0.25 value+0.25]
%          ICAname - name of the algorithm to use in runica (picard as default)
%          epoch_window - start and end time points in seconds of each epoch
%                         a 1*2 vector or 6*2 matrix for each of the ERP
%                         Core TaskLabels {'ERN','MMN','N170','N2pc','N400','P3'}
%                         defaults follow the ERP Core descriptor
%          baseline_window - start and end time points in seconds for baseline correction
%                         a 1*2 vector or 6*2 matrix for each of the ERP
%                         Core TaskLabels {'ERN','MMN','N170','N2pc','N400','P3'}
%          analysis_window - start and end time points in seconds for 1st AnalysisLevel analysis
%                         a 1*2 vector or 6*2 matrix for each of the ERP
%                         Core TaskLabels {'ERN','MMN','N170','N2pc','N400','P3'}
%          estimation - the LIMO procedure to estimate the models' parameters
%                       'WLS' (default) or 'OLS'
%          nboot - the number of bootstrap to execute for the 2nd level
%                  analysis (default 1000, set to 0 for none)
%          tfce - 1 (default) or 0 to additionally compute tfce for the 2nd
%                 level analysis
%
% OUTPUT out lists the new files on drive
%
% Usage example:
%         InputDataset       = '/indirect/staff/cyrilpernet/multiverse_analyses/ERP_CORE_BIDS_Raw_Files'
%         OutputLocation     = fullfile(fileparts(InputDataset),['SIESTA_ERPCore' filesep 'derivatives']); mkdir(OutputLocation);
%         TaskLabel          = {'ERN','MMN'};
%         SubjectLabel       = {'sub-001','sub-002','sub-003','sub-010','sub-011','sub-012','sub-030','sub-031'};
%         first_level_files  = ERP_Core_WB(InputDataset, OutputLocation, '1','TaskLabel',TaskLabel,'SubjectLabel',SubjectLabel)
%         second_level_files = ERP_Core_WB(OutputLocation, [], '2','TaskLabel',TaskLabel)
%
% Cyril Pernet, during the spring of 2024 + various updates by Marcel and
% Jan-Mathijs -- updated Decembre 2024/January 2025 to match BIDS App spec for containarization

% -----------------------------------------------------------------
%% before computing, check inputs, putpuits, dependencies, etc ..
% -----------------------------------------------------------------

if nargin == 0
    help ERP_Core_WB
elseif nargin < 3
    error('at least 3 arguments in are required: InputDataset,OutputLocation,AnalysisLevel')
end

% start eeglab and check plug-ins
rng('default');
ERP_Core_WB_install
current_folder = pwd;

% check basics inputs
if nargin >= 3
    if ~exist(InputDataset,"dir")
        error('input error: %s InputDataset folder does not exist',InputDataset)
    end

    if isnumeric(AnalysisLevel)
        AnalysisLevel = num2str(AnalysisLevel);
    end

    if ~strcmp(AnalysisLevel,{'1','participant','subject','2','group'})
        error('input error: AnalysisLevel must 1 or 2')
    end
    
    if any(strcmp(AnalysisLevel,{'participant','subject'}))
        AnalysisLevel = '1';
    elseif strcmp(AnalysisLevel,'group')
        AnalysisLevel = '2';
    end

    if isempty(OutputLocation)
        if strcmp(AnalysisLevel,'1')
            OutputLocation = fullfile(InputDataset,'derivatives');
        elseif strcmp(AnalysisLevel,'2')
            OutputLocation = InputDataset;
            % error('2nd level analysis must have specified input and output folders')
        end
    end

    if ~exist('OutputLocation','dir')
        mkdir(OutputLocation)
    end
end

options = {};
if nargin>3
    % deal with structure
    if nargin==4 && isstruct(varargin{1})
        tmp = [fieldnames(varargin{1}).'; struct2cell(varargin{1}).'];
        varargin = tmp(:).'; % varargin as cell array as usual 
    end
    
    index = 1;
    for opt =1:2:length(varargin)
        options{index} = varargin{opt}; index = index + 1; %#ok<AGROW>
        if contains(varargin{opt},'TaskLabel','IgnoreCase',true)
            TaskLabel = varargin{opt+1};
        elseif contains(varargin{opt},'SubjectLabel','IgnoreCase',true)
            SubjectLabel = varargin{opt+1};
        end
    end
end

all_sub = dir(fullfile(InputDataset,'sub-*'));
if ~exist('SubjectLabel','var')
    SubjectLabel = arrayfun(@(x) x.name, all_sub, 'UniformOutput', false)';
end
sublist = find(ismember({all_sub.name}', SubjectLabel))'; % labels to num

if ~exist('TaskLabel','var')
        TaskLabel = {'ERN','MMN','N170','N2pc','N400','P3'};
end

if any(cellfun(@(x) contains(x,'high_pass'),options))
    high_pass = varargin{find(cellfun(@(x) contains(x,'high_pass'),options))*2};
else
    high_pass = 0.5;
end

if any(cellfun(@(x) contains(x,'ICAname'),options))
    ICAname = varargin{find(cellfun(@(x) contains(x,'ICAname'),options))*2};
else
    ICAname = 'picard';
end

if any(cellfun(@(x) contains(x,'epoch_window'),options))
    window = varargin{find(cellfun(@(x) contains(x,'epoch_window'),options))*2};
    if all(size(window) == [1 2])
        epoch_window = repmat(window,6,1);
    elseif all(size(window) == [6 2])
        epoch_window = window;
    else
        error('wrong epoch window input size')
    end
else
    epoch_window(1,:)   = [-0.6 0.4]; % pop_epoch
    epoch_window(2:6,:) = repmat([-0.2 0.8],5,1);
end

if any(cellfun(@(x) contains(x,'baseline_window'),options))
    window = varargin{find(cellfun(@(x) contains(x,'baseline_window'),options))*2};
    if all(size(window) == [1 2])
        baseline_window = repmat(window,6,1);
    elseif all(size(window) == [6 2])
        baseline_window = window;
    else
        error('wrong baseline window input size')
    end
else
    baseline_window(1,:)   = [-400 -200]; % std_precomp
    baseline_window(2:6,:) = repmat([-200 0],5,1);
end

if any(cellfun(@(x) contains(x,'analysis_window'),options))
    window = varargin{find(cellfun(@(x) contains(x,'analysis_window'),options))*2};
    if all(size(window) == [1 2])
        analysis_window = repmat(window,6,1);
    elseif all(size(window) == [6 2])
        analysis_window = window;
    else
        error('wrong analysis window input size')
    end
else
    analysis_window(1,:)   = [-200 400];  % pop_limo
    analysis_window(2:6,:) = repmat([-200 600],5,1);
end

if any(cellfun(@(x) contains(x,'estimation'),options))
   estimation = varargin(find(cellfun(@(x) contains(x,'estimation'),options))*2);
    if ~any(strcmpi(estimation,{'OLS','WLS','IRLS'}))
        error('estimation value invalid')
    end
else
    estimation = 'WLS';
end

if any(cellfun(@(x) contains(x,'nboot'),options))
    nboot = varargin{find(cellfun(@(x) strcmp(x,'nboot'),options))*2};    
else
    nboot = 1000;
end

if any(cellfun(@(x) contains(x,'tfce'),options))
    tfce = varargin{find(cellfun(@(x) strcmp(x,'tfce'),options))*2};
    if tfce >1 || ~isnumeric(single(tfce)) % add single in case of boolean
        error('tfce value must be set to 1 or 0 (currently %g\n)',tfce)
    end
else
    tfce = 0;
end

% -----------------------------------------------------------------
%% Compute 1st level analyses
% -----------------------------------------------------------------

if strcmpi(AnalysisLevel,'1')
    out.AnalysisLevel = 1;

    % edit participants.tsv checking the same subjects are present
    participants = readtable(fullfile(InputDataset,'participants.tsv'), 'FileType', 'text', ...
        'Delimiter', '\t', 'TreatAsEmpty', {'N/A','n/a'}); N = size(participants,1);
    for p=length(participants.participant_id):-1:1
        name_match(:,p) = arrayfun(@(x) strcmpi(x.name,participants.participant_id{p}),all_sub);
    end

    if ~isempty(find(sum(name_match,1)==0)) %#ok<EFIND>
        participants(find(sum(name_match,1)==0),:) = []; %#ok<FNDSB>
        warning('mismatch between files and participants.tsv -%g subject(s)',N-size(participants,1))
        writetable(participants, fullfile(InputDataset,'participants.tsv'), 'FileType', 'text', 'Delimiter', '\t');
    end

    % edit events.tsv files
    % should we correct epoching +26ms for stimuli from events.tsv files? as opposed to eeg channels

    % edit events.tsv files for meaningful epoching for N170
    if any(contains(TaskLabel,'N170'))
        for sub = 1:size(all_sub,1)
            root   = fullfile(all_sub(sub).folder,[all_sub(sub).name filesep 'ses-N170' filesep 'eeg']);
            file   = [all_sub(sub).name,'_ses-N170_task-N170_events.tsv'];
            if exist(fullfile(root,file),'file')
                events = readtable(fullfile(root,file), 'FileType', 'text', ...
                    'Delimiter', '\t', 'TreatAsEmpty', {'N/A','n/a'});
                for s = size(events,1):-1:1
                    if events.value(s) <= 40
                        event{s} = 'faces';
                    elseif (events.value(s) >= 41) && (events.value(s) < 101)
                        event{s} = 'cars';
                    elseif (events.value(s) >= 101) && (events.value(s) < 141)
                        event{s} = 'scrambled_faces';
                    else
                        event{s} = 'scrambled_cars';
                    end
                end
                t = table(events.onset,events.duration,events.sample,events.trial_type,event',events.value,...
                    'VariableNames',{'onset', 'duration', 'sample', 'trial_type', 'event', 'value'});
                writetable(t, fullfile(root,file), 'FileType', 'text', 'Delimiter', '\t');
                clear event events t
            end
        end
    end

    % loop by TaskLabel
    for t = 1:length(TaskLabel)

        %% IMPORT
        outdir = fullfile(OutputLocation); % ,TaskLabel{t});
        if ~exist(outdir,'dir')
            mkdir(outdir)
        end

        if strcmpi(TaskLabel{t},'N170')
            [STUDY, ALLEEG] = pop_importbids(InputDataset, 'bidsevent','on','bidschanloc','on', ...
                'bidstask',TaskLabel{t},'eventtype', 'event', 'outputdir' ,outdir, 'studyName',TaskLabel{t}, 'subjects', sublist);
        else
            [STUDY, ALLEEG] = pop_importbids(InputDataset, 'bidsevent','on','bidschanloc','on', ...
                'bidstask',TaskLabel{t},'eventtype', 'value', 'outputdir' ,outdir, 'studyName',TaskLabel{t}, 'subjects', sublist);
        end
        
        if t == 1 % also export metadata
            addpath([fileparts(which('pop_importbids.m')) filesep 'JSONio']);
            json = jsonread([InputDataset filesep 'dataset_description.json']);
            json.DatasetType = 'Derivative';
            json.Authors = 'Cyril Pernet';
            json.SourceDatasets = "https://osf.io/9f5w7/files/osfstorage";
            jsonwrite(fullfile(outdir,'dataset_description.json'),json,'prettyprint','on');
            % ignore extra files
            lines = {'*.study', '*.mat'};
            fid = fopen([outdir filesep '.bidsignore'], 'w');
            if fid == -1
                error('Cannot open .bidsignore for writing.');
            else
                for i = 1:length(lines)
                    fprintf(fid, '%s\n', lines{i});
                end
                fclose(fid);
            end
        end

        if length(ALLEEG) == 1 %#ok<ISCL>
            ALLEEG = eeg_checkset(ALLEEG, 'loaddata');
        end
        ALLEEG = pop_select( ALLEEG, 'nochannel',{'HEOG_left','HEOG_right','VEOG_lower'});
        STUDY = pop_statparams(STUDY, 'default');

        % usually do this - but because it run one subject at a time 
        % to create the differential privacy results, we just load one that
        % was precomputed and reuse it all the time
        % [STUDY,~,AvgChanlocs] = std_prepare_neighbors(STUDY, ALLEEG, 'force', 'on');
        % remove connections 8-9/3 ie P7-P9/F7, 26-27/19 ie P8-P10/F8 and 7-25/22 ie P3-P4/Cz
        % pairs(1,:) = [3 8];   pairs(2,:) = [3 9];
        % pairs(3,:) = [19 26]; pairs(4,:) = [19 27];
        % pairs(5,:) = [7 22];  pairs(6,:) = [25 22];
        % for p=1:6
        %    AvgChanlocs.channeighbstructmat(pairs(p,1),pairs(p,2)) = 0;
        %    AvgChanlocs.channeighbstructmat(pairs(p,2),pairs(p,1)) = 0;
        % end
        % save(fullfile(outdir, [TaskLabel{t} '-AvgChanlocs.mat']),'AvgChanlocs')
        localdir    = fileparts(which('ERP_Core_WB.m'));
        AvgChanlocs = load(fullfile(localdir, 'limo-AvgChanlocs.mat'));
        AvgChanlocs = AvgChanlocs.AvgChanlocs; 

        %% Pre-processing
        % for each subject, downsample, clean 50Hz, remove bad channels,
        % interpolate, re-reference to the average, run ICA to remove
        % eye and muscle artefacts, delete bad segments

        EEG = ALLEEG;
        for s=1:size(ALLEEG,2)
            try
                % downsample
                EEGTMP = eeg_checkset(EEG(s), 'loaddata');
                if EEGTMP.srate ~= 250
                    EEGTMP = pop_resample(EEGTMP, 250);
                end
                % line freq removal
                EEGTMP = pop_zapline_plus(EEGTMP,'noisefreqs','line',...
                    'coarseFreqDetectPowerDiff',4,'chunkLength',30,...
                    'adaptiveNremove',1,'fixedNremove',1,'plotResults',0);
                % remove bad channels
                EEGTMP = pop_clean_rawdata(EEGTMP,'FlatlineCriterion',5,'ChannelCriterion',0.8,...
                    'LineNoiseCriterion',4,'Highpass',[high_pass-0.25 high_pass+0.25] ,...
                    'BurstCriterion','off','WindowCriterion','off','BurstRejection','off',...
                    'Distance','Euclidian','WindowCriterionTolerances','off' );
                % interpolate missing channels and reference
                [~,idx] = setdiff({AvgChanlocs.expected_chanlocs.labels},{EEGTMP.chanlocs.labels});
                if ~isempty(idx)
                    EEGTMP = pop_interp(EEGTMP, AvgChanlocs.expected_chanlocs(idx), 'sphericalKang');
                end

               % ICA cleaning
                if strcmpi(ICAname,'picard')
                    EEGTMP = pop_runica(EEGTMP, 'icatype',ICAname,'maxiter',500,'mode','standard','concatcond','on', 'options',{'pca',EEGTMP.nbchan-1});
                else 
                    EEGTMP = pop_runica(EEGTMP, 'icatype',ICAname,'concatcond','on', 'options',{'pca',EEGTMP.nbchan-1});
                end
                EEGTMP = pop_iclabel(EEGTMP, 'default');
                EEGTMP = pop_icflag(EEGTMP,[NaN NaN;0.8 1;0.8 1;NaN NaN;NaN NaN;NaN NaN;NaN NaN]);
                EEGTMP = pop_subcomp(EEGTMP,[],0);

                % clean data using ASR - just the bad segment
                EEGTMP = pop_clean_rawdata(EEGTMP,'FlatlineCriterion','off','ChannelCriterion','off',...
                    'LineNoiseCriterion','off','Highpass','off','BurstCriterion',20,...
                    'WindowCriterion',0.25,'BurstRejection','on','Distance','Euclidian',...
                    'WindowCriterionTolerances',[-Inf 7] );

                % re-reference
                EEGTMP = pop_reref(EEGTMP,[],'interpchan','off');
                EEGTMP = pop_saveset(EEGTMP,'savemode','resave');
                EEG = eeg_store(EEG, EEGTMP, s); % does EEG(s) = EEGTMP but with extra checks
            catch pipe_error
                error_report{s} = pipe_error.message; %#ok<AGROW>
            end
        end

        % Save study
        if exist('error_report','var')
            mask = cellfun(@(x) ~isempty(x), error_report); % which subject/session
            if all(mask)
                save(fullfile(OutputLocation,'error_report_preprocessing'),error_report);
                error('there has been a preprocessing issue with all included datasets, cannot proceed');
            else
                STUDY = std_rmdat(STUDY, EEG, 'datinds', find(mask));
                EEG(mask) = [];
            end
        end
        ALLEEG = EEG;

        %% Statistics
        % Extract data epochs (windowing as per ERP core github)
        if strcmpi(TaskLabel{t},'ERN')
            EEG = pop_epoch(ALLEEG,{'111','112','121','122','211','212','221','222'},...
                epoch_window(t,:) ,'epochinfo','yes');
        elseif strcmpi(TaskLabel{t},'MMN')
            EEG = pop_epoch(ALLEEG,{'80','70'},...
                epoch_window(t,:) ,'epochinfo','yes');
        elseif strcmpi(TaskLabel{t},'N170')
            EEG = pop_epoch(ALLEEG,{'faces','cars','scrambled_faces','scrambled_cars'},...
                epoch_window(t,:) ,'epochinfo','yes');
        elseif strcmpi(TaskLabel{t},'N2pc')
            EEG = pop_epoch(ALLEEG,{'111','112','121','122','211','212','221','222'},...
                epoch_window(t,:) ,'epochinfo','yes');
        elseif strcmpi(TaskLabel{t},'N400')
            EEG = pop_epoch(ALLEEG,{'111','112','121','122','211','212','221','222'},...
                epoch_window(t,:) ,'epochinfo','yes');
        elseif strcmpi(TaskLabel{t},'P3')
            EEG = pop_epoch(ALLEEG,{'11','12','13','14','15','21','22','23','24','25',...
                '31','32','33','34','35','41','42','43','44','45','51','52','53','54','55'},...
                epoch_window(t,:) ,'epochinfo','yes');
        end
        EEG    = eeg_checkset(EEG);
        EEG    = pop_saveset(EEG, 'savemode', 'resave');
        if any(strcmpi(TaskLabel{t},{'ERN','N170'}))
            [STUDY, EEG] = std_editset(STUDY, EEG, 'commands',{{'remove',4}},'updatedat','on','rmclust','on');
        elseif any(strcmpi(TaskLabel{t},{'P3'}))
            [STUDY, EEG] = std_editset(STUDY, EEG, 'commands',{{'remove',4},{'remove',35}},'updatedat','on','rmclust','on');
        end

        % Create study design
        STUDY  = std_checkset(STUDY, EEG);
        STUDY  = std_makedesign(STUDY, EEG, 1, 'name',TaskLabel{t}, ...
            'delfiles','off','defaultdesign','off','variable1','type','values1',{});

        % Precompute ERP measures
        [STUDY, EEG] = std_precomp(STUDY, EEG, {}, 'savetrials','on','interp','on','recompute','on',...
            'erp','on','erpparams', {'rmbase' baseline_window(t,:)}, ...
            'spec','off','ersp','off','itc','off');

        % output preprocessed files 
        for s=size(EEG,2):-1:1
            old = fullfile(EEG(s).filepath,EEG(s).filename(1:end-4));
            EEG(s).setname = 'preprocessed';
            EEG(s).filename = [EEG(s).filename(1:end-7) 'desc-preprocessed_eeg.set'];
            EEG(s) = pop_saveset(EEG(s), 'filename', [EEG(s).filename(1:end-7) 'desc-preprocessed_eeg.set'], 'filepath', EEG(s).filepath);
            STUDY.datasetinfo(s).filename = EEG(s).filename;
            delete([old '.set']);
            delete([old '.fdt']);
            files  = dir(EEG(s).filepath);
            filter = arrayfun(@(x) x.isdir==0, files);
            fullfiles = arrayfun(@(x) fullfile(x.folder,x.name), files(filter), 'UniformOutput', false);
            out.(TaskLabel{t}).participant{s}.preprocessed_files = fullfiles;
        end

        if exist('error_report','var')
            for s=size(EEG,2):-1:1
                if ~isempty(error_report{s})
                    out.(TaskLabel{t}).participant{s}.preprocessed_error = error_report{s};
                end
            end
        end

        % 1st AnalysisLevel analysis
        [STUDY, files] = std_limo(STUDY, EEG, 'method',estimation,...
            'measure','daterp', 'chanloc',AvgChanlocs,...
            'timelim',analysis_window(t,:),'erase','on',...
            'splitreg','off','interaction','off');

        if isempty(STUDY.filepath) % this seems to happen no unknown reason
            STUDY.filepath = outdir;
        end
        STUDY  = std_checkset(STUDY, EEG);
        pop_savestudy(STUDY,EEG,'savemode','resave')

        % add contrasts - which is study specific
        if strcmpi(TaskLabel{t},'ERN')
            % ERN and CRN components are epoched for correct and errors
            % irrespective of the stimulus - make contrasts but check
            % designs, some subject are  missing 'errors'
            % "111": "Response - left, compatible flankers, target left",
            % "112": "Response - left, compatible flankers, target right",
            % "121": "Response - left, incompatible flankers, target left",
            % "122": "Response - left, incompatible flankers, target right",
            % "211": "Response - right, compatible flankers, target left",
            % "212": "Response - right, compatible flankers, target right",
            % "221": "Response - right, incompatible flankers, target left",
            % "222": "Response - right, incompatible flankers, target right"
            ERN = [0 1 0 1 1 0 1 0];
            CRN = [1 0 1 0 0 1 0 1];
            [~,~,LFiles] = limo_get_files([],[],[],...
                fullfile(files.LIMO,'LIMO_files_ERN_ERN_GLM_Channels_Time_WLS.txt'));
            [~,R,BFiles] = limo_get_files([],[],[],...
                fullfile(files.LIMO,'Beta_files_ERN_ERN_GLM_Channels_Time_WLS.txt'));

            for s=length(LFiles):-1:1
                index   = strfind(LFiles{s},'sub-'); % get subject start
                name    = R{s}(index:index+6); % name
                s_value = find(arrayfun(@(x) strcmpi(x.subject,name),STUDY.limo.subjects)); % ensure match
                cond    = unique(STUDY.limo.subjects(s_value).cat_file);
                limo_contrast(fullfile(R{s},[name '_desc-Yr.mat']), BFiles{s}, LFiles{s}, 'T', 1, ERN(cond));
                limo_contrast(fullfile(R{s},[name '_desc-Yr.mat']), BFiles{s}, LFiles{s}, 'T', 1, CRN(cond));
                % con1_files{s,:} = fullfile(R{s},'con_1.mat');
                % con2_files{s,:} = fullfile(R{s},'con_2.mat');
            end
            % writecell(con1_files,fullfile(files.LIMO,'con1_files.txt'))
            % writecell(con2_files,fullfile(files.LIMO,'con2_files.txt'))

        elseif strcmpi(TaskLabel{t},'N170')
            % there are two analyses
            % faces vs cars
            % faces-scrambled vs cars-scrambled
            CarDiff  = [1 0 -1 0];
            FaceDiff = [0 1 0 -1];
            [~,~,LFiles] = limo_get_files([],[],[],...
                fullfile(files.LIMO,'LIMO_files_N170_N170_GLM_Channels_Time_WLS.txt'));
            [~,R,BFiles] = limo_get_files([],[],[],...
                fullfile(files.LIMO,'Beta_files_N170_N170_GLM_Channels_Time_WLS.txt'));

            for s=1:length(LFiles)
                name = R{s}(index:index+6); % name
                limo_contrast(fullfile(R{s},[name '_desc-Yr.mat']), BFiles{s}, LFiles{s}, 'T', 1, CarDiff);
                limo_contrast(fullfile(R{s},[name '_desc-Yr.mat']), BFiles{s}, LFiles{s}, 'T', 1, FaceDiff);
                % con1_files{s,:} = fullfile(R{s},[name '_desc-con_1.mat']);
                % con2_files{s,:} = fullfile(R{s},[name '_desc-con_2.mat']);
            end
            % writecell(con1_files,fullfile(files.LIMO,'con1_files.txt'))
            % writecell(con2_files,fullfile(files.LIMO,'con2_files.txt'))

        elseif strcmpi(TaskLabel{t},'N2pc')
           % "111": "Stimulus - target blue, target left, gap at top",
      	   % "112": "Stimulus - target blue, target left, gap at bottom",
           % "121": "Stimulus - target blue, target right, gap at top",
           % "122": "Stimulus - target blue, target right, gap at bottom",
           % "211": "Stimulus - target pink, target left, gap at top",
           % "212": "Stimulus - target pink, target left, gap at bottom",
           % "221": "Stimulus - target pink, target right, gap at top",
           % "222": "Stimulus - target pink, target right, gap at bottom",
           % for the analysis, make contrasts for left-side targets and right-side targets,
           % but collapsed across target color.
           % then comes, contralateral waveforms (i.e., right hemisphere electrode
           % sites for left-side targets averaged with left hemisphere electrode sites for right-side targets)
           % and ipsilateral waveforms (i.e., right hemisphere electrode sites for right-side targets averaged with
           % left hemisphere electrode sites for left-side targets). We then computed a contralateral-minus-
           % ipsilateral difference waveform to isolate the N2pc. Can be redone using limo_LI.
           left  = [1 1 0 0 1 1 0 0];
           right = [0 0 1 1 0 0 1 1];
           [~,~,LFiles] = limo_get_files([],[],[],...
               fullfile(files.LIMO,'LIMO_files_N2pc_N2pc_GLM_Channels_Time_WLS.txt'));
           [~,R,BFiles] = limo_get_files([],[],[],...
               fullfile(files.LIMO,'Beta_files_N2pc_N2pc_GLM_Channels_Time_WLS.txt'));

           for s=1:length(LFiles)
               index   = strfind(LFiles{s},'sub-'); % get subject start
               name    = R{s}(index:index+6); % name
               s_value = find(arrayfun(@(x) strcmpi(x.subject,name),STUDY.limo.subjects)); % ensure match
               cond    = unique(STUDY.limo.subjects(s_value).cat_file);
               limo_contrast(fullfile(R{s},[name '_desc-Yr.mat']), BFiles{s}, LFiles{s}, 'T', 1, left(cond));
               limo_contrast(fullfile(R{s},[name '_desc-Yr.mat']), BFiles{s}, LFiles{s}, 'T', 1, right(cond));
               % con1_files{s,:} = fullfile(R{s},[name '_desc-con_1.mat']);
               % con2_files{s,:} = fullfile(R{s},[name '_desc-con_2.mat']);
           end
           % writecell(con1_files,fullfile(files.LIMO,'con1_files.txt'))
           % writecell(con2_files,fullfile(files.LIMO,'con2_files.txt'))

        elseif strcmpi(TaskLabel{t},'N400')
           % 111 prime word, related word pair, list 1
     	   % 112 prime word, related word pair, list 2
    	   % 121 prime word, unrelated word pair, list 1
    	   % 122 prime word, unrelated word pair, list 2
    	   % 211 target word, related word pair, list 1
    	   % 212 target word, related word pair, list 2
    	   % 221 target word, unrelated word pair, list 1
    	   % 222 target word, unrelated word pair, list 2
           related   = [0 0 0 0 1 1 0 0];
           unrelated = [0 0 0 0 0 0 1 1];
           [~,~,LFiles] = limo_get_files([],[],[],...
               fullfile(files.LIMO,'LIMO_files_N400_N400_GLM_Channels_Time_WLS.txt'));
           [~,R,BFiles] = limo_get_files([],[],[],...
               fullfile(files.LIMO,'Beta_files_N400_N400_GLM_Channels_Time_WLS.txt'));

           for s=1:length(LFiles)
               index   = strfind(LFiles{s},'sub-'); % get subject start
               name    = R{s}(index:index+6); % name
               s_value = find(arrayfun(@(x) strcmpi(x.subject,name),STUDY.limo.subjects)); % ensure match
               cond    = unique(STUDY.limo.subjects(s_value).cat_file);
               limo_contrast(fullfile(R{s},[name '_desc-Yr.mat']), BFiles{s}, LFiles{s}, 'T', 1, related(cond));
               limo_contrast(fullfile(R{s},[name '_desc-Yr.mat']), BFiles{s}, LFiles{s}, 'T', 1, unrelated(cond));
               % con1_files{s,:} = fullfile(R{s},[name '_desc-con_1.mat']);
               % con2_files{s,:} = fullfile(R{s},[name '_desc-con_2.mat']);
           end
         % writecell(con1_files,fullfile(files.LIMO,'con1_files.txt'))
         % writecell(con2_files,fullfile(files.LIMO,'con2_files.txt'))

        elseif strcmpi(TaskLabel{t},'P3')
         % 11: Stimulus - block target A, trial stimulus A,
       	 % 22: Stimulus - block target B, trial stimulus B,
    	 % 33: Stimulus - block target C, trial stimulus C,
    	 % 44: Stimulus - block target D, trial stimulus D,
         % 55: Stimulus - block target E, trial stimulus E,
         % 12, 13, 14, 15
         % 21, 23, 24, 25
         % 31, 32, 34, 35
         % 41, 42, 43, 45
         % 51, 52, 53, 54
         distractor = [0 1 1 1 1 1 0 1 1 1 1 1 0 1 1 1 1 1 0 1 1 1 1 1 0];
         target     = distractor==0;
         [~,~,LFiles] = limo_get_files([],[],[],...
             fullfile(files.LIMO,'LIMO_files_P3_P3_GLM_Channels_Time_WLS.txt'));
         [~,R,BFiles] = limo_get_files([],[],[],...
             fullfile(files.LIMO,'Beta_files_P3_P3_GLM_Channels_Time_WLS.txt'));

         for s=1:length(LFiles)
             index   = strfind(LFiles{s},'sub-'); % get subject start
             name    = R{s}(index:index+6); % name
             s_value = find(arrayfun(@(x) strcmpi(x.subject,name),STUDY.limo.subjects)); % ensure match
             cond    = unique(STUDY.limo.subjects(s_value).cat_file);
             limo_contrast(fullfile(R{s},[name '_desc-Yr.mat']), BFiles{s}, LFiles{s}, 'T', 1, distractor(cond));
             limo_contrast(fullfile(R{s},[name '_desc-Yr.mat']), BFiles{s}, LFiles{s}, 'T', 1, target(cond));
             % con1_files{s,:} = fullfile(R{s},[name '_desc-con_1.mat']);
             % con2_files{s,:} = fullfile(R{s},[name '_desc-con_2.mat']);
         end
         % writecell(con1_files,fullfile(files.LIMO,'con1_files.txt'))
         % writecell(con2_files,fullfile(files.LIMO,'con2_files.txt'))
        end 

        %% clean-up to format at a BIDS derivatives dataset
        % move directory up LIMO.mat, betas and con files
        for s=size(EEG,2):-1:1
            subfolder  = [extractBefore(files.mat{s},[filesep 'derivatives']) cell2mat(extractBetween(files.mat{s},'derivatives','eeg')) 'eeg'];
            LIMOfiles  = dir(fileparts(files.mat{s}));
            filter     = arrayfun(@(x) x.isdir==0, LIMOfiles);
            fullfiles  = arrayfun(@(x) fullfile(x.folder,x.name), LIMOfiles(filter), 'UniformOutput', false);
            files2move = find(contains(fullfiles,{'LIMO.mat','Betas.mat','con'}));
            for f=1:length(files2move)
                [~,filename,ext] = fileparts(fullfiles{files2move(f)});
                movefile(fullfiles{files2move(f)},fullfile(subfolder,[filename,ext]),'f');                
                out.(TaskLabel{t}).participant{s}.glm_files{f} = fullfile(subfolder,[filename,ext]);
            end            
        end  
        
        clear STUDY ALLEEG EEG error_report
        cd(current_folder)
    end
end

% -----------------------------------------------------------------
%% Compute 2nd level analyses
% -----------------------------------------------------------------

if strcmpi(AnalysisLevel,'2')
    out.AnalysisLevel = 2;
    indir = InputDataset; 

    % BIDS derivatives dataset is the input
    % ---------------------------------------
    if length(TaskLabel) == 6
        subjects = dir(fullfile(indir,'sub-*'));
        if isempty(subjects)
            error('there are no subjects in the specified input folder')
        else
            for s= size(subjects,1):-1:1
                ses_folders = dir(fullfile(subjects(s).folder,[subjects(s).name filesep 'ses-*']));
                tasks = arrayfun(@(x) extractAfter(x.name,'ses-'), ses_folders,"UniformOutput",false);
                checks(:,s) = cellfun(@(x) any(strcmpi(x,tasks)), TaskLabel);
            end
            TaskLabel(sum(checks,2)==0) = []; % remove missing tasks
        end
    end

    % load neighbouring matrix
    localdir    = fileparts(which('ERP_Core_WB.m'));
    AvgChanlocs = load(fullfile(localdir, 'limo-AvgChanlocs.mat'));
    AvgChanlocs = AvgChanlocs.AvgChanlocs; 

    for t = 1:length(TaskLabel)

        % output
        if ~contains(OutputLocation,'group')
            outdir = fullfile(OutputLocation,'group');mkdir(outdir);
        else
            outdir = OutputLocation;
        end

        % start processing
        if strcmpi(TaskLabel{t},'ERN')
            
            % make con_files list manually since 1st and 2nd level are disjointed
            con1_files = getconfiles(indir,'ERN','1');
            % con2_files = getconfiles(indir,'ERN','2');
            % LIMO_files = getLIMOfiles(indir,'ERN');
            taskdir    = fullfile(extractBefore(outdir,'group'),'LIMO_ERN');
            % for c = 1:3
            %     if c == 1
                    resultdir = fullfile(taskdir,'ERN');
                    mkdir(resultdir);
                    cd(resultdir);
                    limo_random_select('one sample t-test',AvgChanlocs,...
                        'LIMOfiles',con1_files,'parameter',1, 'analysis_type',...
                        'Full scalp analysis', 'type','Channels','nboot',0,'tfce',tfce);
            %         % limo_get_effect_size('One_Sample_Ttest_parameter_1.mat')
            %         % mean contrast values
            %         % limo_central_tendency_and_ci(con1_files,...
            %         %     1, AvgChanlocs.expected_chanlocs, 'mean', 'Trimmed mean', 21,'FCz_ERP')                    
            results = load(fullfile(resultdir,'One_Sample_Ttest_parameter_1.mat'));       
            tvalues = squeeze(results.one_sample(:,:,4)); % t values
            save(fullfile(outdir,'task-ERN_desc-OneSampleTTtestERN.mat'),'tvalues');
            out.(TaskLabel{t}).ERN = get_rfxfiles(pwd);
            %     elseif c == 2
            %         resultdir = fullfile(taskdir,'CRN');
            %         mkdir(resultdir);
            %         cd(resultdir);
            %         limo_random_select('one sample t-test',AvgChanlocs,...
            %             'LIMOfiles',con2_files,'parameter',1, 'analysis_type',...
            %             'Full scalp analysis', 'type','Channels','nboot',nboot,'tfce',tfce);
            %         % limo_get_effect_size('one_sample_ttest_parameter_1.mat')
            %         % mean contrast values
            %         % limo_central_tendency_and_ci(con2_files,...
            %         %     1, AvgChanlocs.expected_chanlocs, 'mean', 'Trimmed mean', 21,'FCz_ERP')
            %         copyfile(fullfile(resultdir,'One_Sample_Ttest_parameter_1.mat'),...
            %             fullfile(outdir,'task-ERN_desc-OneSampleTTtestCRN.mat'));
            %         out.(TaskLabel{t}).CRN = get_rfxfiles(pwd);
            %     else
                    % resultdir = fullfile(taskdir,'Difference_wave');
                    % mkdir(resultdir);
                    % cd(resultdir);
                    % for N=length(con1_files):-1:1
                    %     data{1,N} = con1_files{N};
                    %     data{2,N} = con2_files{N};
                    % end
                    % limo_random_select('paired t-test',AvgChanlocs,...
                    %     'LIMOfiles',data, 'analysis_type',...
                    %     'Full scalp analysis', 'type','Channels','nboot',nboot,'tfce',tfce);
                    % % limo_get_effect_size('paired_samples_ttest_parameter_1_2.mat')
                    % ERPs (does not work without coying data Yr in BIDS derivatives)
                    % ERN = [0 1 0 1 1 0 1 0];
                    % CRN = [1 0 1 0 0 1 0 1];
                    % limo_central_tendency_and_ci(LIMO_files, ...
                    %     find(ERN), AvgChanlocs, 'Weighted mean', 'Trimmed mean', [], 'ERPs_errors')
                    % limo_central_tendency_and_ci(LIMO_files, ...
                    %     find(CRN), AvgChanlocs, 'Weighted mean', 'Trimmed mean', [], 'ERPs_correct')
                    % Diff = limo_plot_difference('ERPs_errors_single_subjects_Weighted mean.mat',...
                    %     'ERPs_correct_single_subjects_Weighted mean.mat',...
                    %     'type','paired','fig',0,'name','ERP_diff');
                    % save('ERP_difference','Diff')
                    % copyfile(fullfile(resultdir,'Paired_Samples_Ttest_parameter_1_2.mat'),...
                    %     fullfile(outdir,'task-ERN_desc-PairedSamplesTTestDifferenceWave.mat'));
                    % out.(TaskLabel{t}).Difference_wave = get_rfxfiles(pwd);
            %     end
            % end

        elseif strcmpi(TaskLabel{t},'MMN')

            taskdir    = fullfile(extractBefore(outdir,'group'),'LIMO_MMN');
            resultdir = fullfile(taskdir,'MMN');
            mkdir(resultdir);
            cd(resultdir);
            Beta_files = getBetafiles(indir,'MMN');
            writecell(Beta_files', 'allBetas.txt', 'Delimiter', ' ');
            limo_random_select('paired t-test',AvgChanlocs,...
                'LIMOfiles','allBetas.txt', 'parameter',[1 2], 'analysis_type',...
                'Full scalp analysis', 'type','Channels','nboot',0,'tfce',tfce);
            % limo_get_effect_size('paired_samples_ttest_parameter_1_2.mat')
            % ERPs (use limo_add_plots to visualize)
            % limo_central_tendency_and_ci(fullfile(fullfile(indir,['LIMO_' TaskLabel{t}]),'LIMO_files_MMN_MMN_GLM_Channels_Time_WLS.txt'), ...
            %     1, AvgChanlocs, 'Weighted mean', 'Trimmed mean', [], 'ERPs_deviant')
            % limo_central_tendency_and_ci(fullfile(fullfile(indir,['LIMO_' TaskLabel{t}]),'LIMO_files_MMN_MMN_GLM_Channels_Time_WLS.txt'), ...
            %     2, AvgChanlocs, 'Weighted mean', 'Trimmed mean', [], 'ERPs_standard')
            % Diff = limo_plot_difference('ERPs_deviant_single_subjects_Weighted mean.mat',...
            %     'ERPs_standard_single_subjects_Weighted mean.mat',...
            %     'type','paired','fig',0,'name','ERP_MMN');
            % save('ERP_difference','Diff')
            results = load(fullfile(resultdir,'Paired_Samples_Ttest_parameter_1_2.mat'));
            tvalues = squeeze(results.paired_samples(:,:,4)); % t values
            save(fullfile(outdir,'task-MMN_desc-PairedSamplesTTest.mat'),'tvalues');
            out.(TaskLabel{t}).MMN = get_rfxfiles(pwd);

        elseif strcmpi(TaskLabel{t},'N170')

            taskdir    = fullfile(extractBefore(outdir,'group'),'LIMO_N170');
            resultdir = fullfile(taskdir,'N170');
            mkdir(resultdir);
            cd(resultdir);
            Beta_files = getBetafiles(indir,'N170');
            writecell(Beta_files', 'allBetas.txt', 'Delimiter', ' ');
            mkdir(fullfile(resultdir,'Cars_vs_Faces'));
            cd(fullfile(resultdir,'Cars_vs_Faces'));
            limo_random_select('paired t-test',AvgChanlocs,...
                'LIMOfiles',fullfile(resultdir,'allBetas.txt'), 'parameter',[2 1], 'analysis_type',...
                'Full scalp analysis', 'type','Channels','nboot',0,'tfce',tfce);
            limo_get_effect_size('Paired_Samples_Ttest_parameter_2_1.mat')
            % ERPs (use limo_add_plots to visualize)
            % limo_central_tendency_and_ci(fullfile(fullfile(indir,['LIMO_' TaskLabel{t}]),'LIMO_files_N170_N170_GLM_Channels_Time_WLS.txt'), ...
            %     1, AvgChanlocs, 'Weighted mean', 'Trimmed mean', [], 'ERPs_Cars')
            % limo_central_tendency_and_ci(fullfile(fullfile(indir,['LIMO_' TaskLabel{t}]),'LIMO_files_N170_N170_GLM_Channels_Time_WLS.txt'), ...
            %     2, AvgChanlocs, 'Weighted mean', 'Trimmed mean', [], 'ERPs_Faces')
            % Diff = limo_plot_difference('ERPs_Faces_single_subjects_Weighted mean.mat',...
            %     'ERPs_Cars_single_subjects_Weighted mean.mat',...
            %     'type','paired','fig',0,'name','ERP_Difference');
            % save('ERP_difference','Diff')
            copyfile(fullfile([resultdir filesep 'Cars_vs_Faces'],'Paired_Samples_Ttest_parameter_2_1_Cohensd.mat'),...
                fullfile(outdir,'task-N170_desc-PairedSamplesTTestEffectSizeCarsFaces.mat'));
            out.(TaskLabel{t}).N170.Cars_vs_Faces = get_rfxfiles(pwd);

            % con1_files = getconfiles(indir,'N170','1');
            % con2_files = getconfiles(indir,'N170','2');
            % mkdir(fullfile(resultdir,'Cars_vs_Faces_controlled'));
            % cd(fullfile(resultdir,'Cars_vs_Faces_controlled'));
            % for N=size(con1_files,1):-1:1
            %     data{1,N} = con1_files{N};
            %     data{2,N} = con2_files{N};
            % end
            % limo_random_select('paired t-test',AvgChanlocs,...
            %     'LIMOfiles',data, 'analysis_type',...
            %     'Full scalp analysis', 'type','Channels','nboot',nboot,'tfce',tfce);
            % limo_get_effect_size('paired_samples_ttest_parameter_1_2.mat')
            % Param avg (use limo_add_plots to visualize)
            % we can also do double diff ERP if needed (do as above twice)
            % limo_central_tendency_and_ci(fullfile([indir filesep 'LIMO_' TaskLabel{t}],'con1_files.txt'),...
            %     1, AvgChanlocs, 'mean', 'Trimmed mean', [],'Con_Cars')
            % limo_central_tendency_and_ci(fullfile([indir filesep 'LIMO_' TaskLabel{t}],'con2_files.txt'),...
            %     1, AvgChanlocs, 'mean', 'Trimmed mean', [],'Con_Faces')
            % Diff = limo_plot_difference('Con_Faces_single_subjects_mean.mat',...
            %     'Con_Cars_single_subjects_mean.mat',...
            %     'type','paired','fig',0,'name','Con_diff');
            % save('Parameter_difference','Diff')
            % limo_central_tendency_and_ci(fullfile(fullfile(indir,['LIMO_' TaskLabel{t}]),'LIMO_files_N170_N170_GLM_Channels_Time_WLS.txt'), ...
            %     1 , AvgChanlocs, 'Weighted mean', 'Trimmed mean', [], 'ERPs_Cars')
            % limo_central_tendency_and_ci(fullfile(fullfile(indir,['LIMO_' TaskLabel{t}]),'LIMO_files_N170_N170_GLM_Channels_Time_WLS.txt'), ...
            %     3, AvgChanlocs, 'Weighted mean', 'Trimmed mean', [], 'ERPs_Cars_control')
            % set1      = load('ERPs_Cars_single_subjects_Weighted mean.mat');
            % set2      = load('ERPs_Cars_control_single_subjects_Weighted mean.mat');
            % Data.data = set1.Data.data - set2.Data.data;
            % Data.limo = set1.Data.limo;
            % save('ERPs_Cars_diff_single_subjects_Weighted mean.mat','Data')
            % limo_central_tendency_and_ci(fullfile(fullfile(indir,['LIMO_' TaskLabel{t}]),'LIMO_files_N170_N170_GLM_Channels_Time_WLS.txt'), ...
            %     2, AvgChanlocs, 'Weighted mean', 'Trimmed mean', [], 'ERPs_Faces')
            % limo_central_tendency_and_ci(fullfile(fullfile(indir,['LIMO_' TaskLabel{t}]),'LIMO_files_N170_N170_GLM_Channels_Time_WLS.txt'), ...
            %     4, AvgChanlocs, 'Weighted mean', 'Trimmed mean', [], 'ERPs_Faces_control')
            % set1      = load('ERPs_Faces_single_subjects_Weighted mean.mat');
            % set2      = load('ERPs_Faces_control_single_subjects_Weighted mean.mat');
            % Data.data = set1.Data.data - set2.Data.data;
            % Data.limo = set1.Data.limo;
            % save('ERPs_Faces_diff_single_subjects_Weighted mean.mat','Data')
            % Diff = limo_plot_difference('ERPs_Faces_diff_single_subjects_Weighted mean.mat',...
            %     'ERPs_Cars_diff_single_subjects_Weighted mean.mat',...
            %     'type','paired','fig',0,'name','ERP_Faces_Cars_Difference');
            % save('ERP_difference','Diff')

        elseif strcmpi(TaskLabel{t},'N2pc')

            taskdir    = fullfile(extractBefore(outdir,'group'),'LIMO_N2pc');
            resultdir = fullfile(taskdir,'N2pc');
            mkdir(resultdir);
            cd(resultdir);
            
            con1_files = getconfiles(indir,'N2pc','1'); writecell(con1_files', 'allcon1.txt', 'Delimiter', ' ');
            con2_files = getconfiles(indir,'N2pc','2'); writecell(con2_files', 'allcon2.txt', 'Delimiter', ' ');
            labels = arrayfun(@(x) x.labels, AvgChanlocs.expected_chanlocs, 'UniformOutput', false);
            table_channels{1} = labels(1:12)'; table_channels{2} = labels([16 18 19 20 23:30])';
            channels = limo_pair_channels(AvgChanlocs.expected_chanlocs,'pairs',table_channels,'figure','off');
            limo_ipsi_contra('allcon1.txt','allcon2.txt',...
                'channellocs',AvgChanlocs,'channelpairs',channels,0,0)
            % limo_get_effect_size('paired_samples_ttest_parameter_1_2.mat')
            load LIMO.mat %#ok<LOAD>
            if ~isfield(LIMO.data,'timevect')
                LIMO.data.timevect = LIMO.data.start:(1/LIMO.data.sampling_rate*1000):LIMO.data.end;
                save(fullfile(LIMO.dir,'LIMO.mat'),'LIMO');
            end
            load('ipsilateral.mat'); %#ok<LOAD> % TM1  = limo_trimmed_mean(ipsilateral,20,.05); %#ok<LOAD>
            load('contralateral.mat'); %#ok<LOAD> % TM2  = limo_trimmed_mean(contralateral,20,.05); %#ok<LOAD>
            Diff = limo_trimmed_mean(contralateral-ipsilateral,20,.05);
            save('ERP_difference','Diff')

            % figure;
            % channel = 10; % use PO7/PO8
            % subplot(1,2,1); vect = LIMO.data.timevect; hold on
            % plot(vect,squeeze(TM1(channel,:,2)),'LineWidth',2,'Color',[1 0 0]);
            % plot(vect,squeeze(TM2(channel,:,2)),'LineWidth',2,'Color',[0 0 1]);
            % fillhandle = patch([vect fliplr(vect)], [squeeze(TM1(channel,:,1)) ,fliplr(squeeze(TM1(channel,:,3)))], [1 0 0]);
            % set(fillhandle,'EdgeColor',[1 0 0],'FaceAlpha',0.2,'EdgeAlpha',0.8);%set edge color
            % fillhandle = patch([vect fliplr(vect)], [squeeze(TM2(channel,:,1)) ,fliplr(squeeze(TM2(channel,:,3)))], [0 0 1]);
            % set(fillhandle,'EdgeColor',[0 0 1],'FaceAlpha',0.2,'EdgeAlpha',0.8);%set edge color
            % grid on; axis tight; box on; title('Trimmed means - N2Pc for channels PO7/PO8')
            % legend({'ipsilateral conditions','contralateral conditions'});
            % subplot(1,2,2);
            % plot(vect,squeeze(Diff(channel,:,2)),'LineWidth',2,'Color',[0 0 1]);
            % fillhandle = patch([vect fliplr(vect)], [squeeze(Diff(channel,:,1)) , ...
            %     fliplr(squeeze(Diff(channel,:,3)))], [1 0 0]);
            % set(fillhandle,'EdgeColor',[1 0 0],'FaceAlpha',0.2,'EdgeAlpha',0.8);%set edge color
            % grid on; axis tight; box on; title('contra minus ipsi for channels PO7/PO8')
            % saveas(gcf, 'PO7_PO8_difference.fig','fig'); close(gcf)
            copyfile(fullfile(resultdir,'ERP_difference.mat'),...
                fullfile(outdir,'task-N2pc_desc-ERP_difference.mat'));            
            out.(TaskLabel{t}).N2pc = get_rfxfiles(pwd);

        elseif strcmpi(TaskLabel{t},'N400')
            
            taskdir    = fullfile(extractBefore(outdir,'group'),'LIMO_N400');
            resultdir = fullfile(taskdir,'N400');
            mkdir(resultdir);
            cd(resultdir);
            
            % con1_files = getconfiles(indir,'N400','1'); 
            % con2_files = getconfiles(indir,'N400','2'); 
            % for N=size(con1_files,2):-1:1
            %     data{1,N} = con1_files{N};
            %     data{2,N} = con2_files{N};
            % end
            % limo_random_select('paired t-test',AvgChanlocs,...
            %     'LIMOfiles',data, 'analysis_type',...
            %     'Full scalp analysis', 'type','Channels','nboot',nboot,'tfce',tfce);
            % limo_get_effect_size('paired_samples_ttest_parameter_1_2.mat')
            % Param avg (use limo_add_plots to visualize)
            % limo_central_tendency_and_ci(con1_files,...
            %     1, AvgChanlocs, 'mean', 'Trimmed mean', [],'Con_related')
            % limo_central_tendency_and_ci(con2_files,...
            %     1, AvgChanlocs, 'mean', 'Trimmed mean', [],'Con_unrelated')
            % Diff = limo_plot_difference('Con_unrelated_single_subjects_mean.mat',...
            %     'Con_related_single_subjects_mean.mat',...
            %     'type','paired','fig',0,'name','Con_diff');
            % save('Parameter_difference','Diff')
            LIMO_files = getLIMOfiles(indir,'N400'); writecell(LIMO_files', 'allLIMOs.txt', 'Delimiter', ' ');
            limo_central_tendency_and_ci(fullfile(resultdir,'allLIMOs.txt'),...
                'con_1', AvgChanlocs, 'Weighted mean', 'Trimmed mean', [], 'ERPs_related')
            limo_central_tendency_and_ci(fullfile(resultdir,'allLIMOs.txt'),...
                'con_2', AvgChanlocs, 'Weighted mean', 'Trimmed mean', [], 'ERPs_unrelated')
            limo_plot_difference('ERPs_unrelated_single_subjects_Weighted mean.mat',...
                'ERPs_related_single_subjects_Weighted mean.mat',...
                'type','paired','fig',0,'name','ERP_difference');
            results = load(fullfile(resultdir,'ERP_difference.mat'));
            Diff = results.Data.Diff;
            save(fullfile(outdir,'task-N400_desc-ERP_difference.mat'),'Diff');            
            out.(TaskLabel{t}).N400 = get_rfxfiles(pwd);

        elseif strcmpi(TaskLabel{t},'P3')

            taskdir    = fullfile(extractBefore(outdir,'group'),'LIMO_P3');
            resultdir = fullfile(taskdir,'P3');
            mkdir(resultdir);
            cd(resultdir);
            
            con1_files = getconfiles(indir,'P3','1');
            con2_files = getconfiles(indir,'P3','2');
            for N=size(con1_files,2):-1:1
                data{1,N} = con2_files{N};
                data{2,N} = con1_files{N};
            end
            limo_random_select('paired t-test',AvgChanlocs,...
                'LIMOfiles',data, 'analysis_type',...
                'Full scalp analysis', 'type','Channels','nboot',nboot,'tfce',tfce);
            LIMO = load('LIMO.mat');
            [~, mask] = limo_stat_values('Paired_Samples_Ttest_parameter_2_1.mat',...
                0.05,2,LIMO.LIMO);
            stats = load('Paired_Samples_Ttest_parameter_2_1.mat');
            results = stats.paired_samples(:,:,4) .* (mask>0);
            results(results==0) = NaN;
            save('signitifcant_values','results');
            copyfile(fullfile(resultdir,'signitifcant_values.mat'),...
                fullfile(outdir,'task-P3_desc-significant_values.mat'));            
            out.(TaskLabel{t}).P3 = get_rfxfiles(pwd);
            % limo_get_effect_size('paired_samples_ttest_parameter_2_1.mat')
            % % Param avg (use limo_add_plots to visualize)
            % limo_central_tendency_and_ci(fullfile([indir filesep 'LIMO_' TaskLabel{t}],'con1_files.txt'),...
            %     1, AvgChanlocs, 'mean', 'Trimmed mean', [],'Con_distractors')
            % limo_central_tendency_and_ci(fullfile([indir filesep 'LIMO_' TaskLabel{t}],'con2_files.txt'),...
            %     1, AvgChanlocs, 'mean', 'Trimmed mean', [],'Con_targets')
            % Diff = limo_plot_difference('Con_targets_single_subjects_mean.mat',...
            %     'Con_distractors_single_subjects_mean.mat',...
            %     'type','paired','fig',0,'name','Con_diff');
            % save('Parameter_difference','Diff')
            % limo_central_tendency_and_ci(fullfile(fullfile(indir,['LIMO_' TaskLabel{t}]),'LIMO_files_P3_P3_GLM_Channels_Time_WLS.txt'),...
            %     'con_1', AvgChanlocs, 'Weighted mean', 'Trimmed mean', [], 'ERPs_distractors')
            % limo_central_tendency_and_ci(fullfile(fullfile(indir,['LIMO_' TaskLabel{t}]),'LIMO_files_P3_P3_GLM_Channels_Time_WLS.txt'),...
            %     'con_2', AvgChanlocs, 'Weighted mean', 'Trimmed mean', [], 'ERPs_targets')
            % Diff = limo_plot_difference('ERPs_targets_single_subjects_Weighted mean.mat',...
            %     'ERPs_distractors_single_subjects_Weighted mean.mat',...
            %     'type','paired','fig',0,'name','ERP_diff');
            % save('ERP_difference','Diff')
            
        end
        clear STUDY ALLEEG EEG
        cd(current_folder)
    end
end

% routine to list beta files
function Beta_file = getBetafiles(indir,task)

subjects = dir(fullfile(indir,'sub-*'));
subject_index = 1;
for s= size(subjects,1):-1:1
    foundfile = dir(fullfile(subjects(s).folder,[subjects(s).name filesep 'ses-' task ...
        filesep 'eeg' filesep 'sub*-Betas.mat']));
    if ~isempty(foundfile)
        Beta_file{subject_index} = fullfile(foundfile.folder,foundfile.name);
        subject_index = subject_index +1;
    end
end

% routine to list con files
function con_file = getconfiles(indir,task,connumber)

subjects = dir(fullfile(indir,'sub-*'));
subject_index = 1;
for s= size(subjects,1):-1:1
    foundfile = dir(fullfile(subjects(s).folder,[subjects(s).name filesep 'ses-' task ...
        filesep 'eeg' filesep 'sub*-con_' connumber '.mat']));
    if ~isempty(foundfile)
        con_file{subject_index} = fullfile(foundfile.folder,foundfile.name);
        subject_index = subject_index +1;
    end
end

% routine to list LIMO files
function LIMO_file = getLIMOfiles(indir,task)

subjects = dir(fullfile(indir,'sub-*'));
subject_index = 1;
for s= size(subjects,1):-1:1
    foundfile = dir(fullfile(subjects(s).folder,[subjects(s).name filesep 'ses-' task ...
        filesep 'eeg' filesep 'LIMO.mat']));
    if ~isempty(foundfile)
        LIMO_file{subject_index} = fullfile(foundfile.folder,foundfile.name);
        subject_index = subject_index +1;
    end
end

% routine to list files at second level, returned in out 
function files = get_rfxfiles(folder)

all_files = dir(fullfile(folder,'*.mat'));
files = arrayfun(@(x) fullfile(folder,x.name), all_files, 'UniformOutput', false);

if exist(fullfile(folder,'tfce'),'dir')
    tfce_files = dir(fullfile(fullfile(folder,'tfce'),'*.mat'));
    tfce_files = arrayfun(@(x) fullfile(x.folder,x.name), tfce_files, 'UniformOutput', false);
    files    = [files; tfce_files];
end

if exist(fullfile(folder,'H0'),'dir')
    H0_files = dir(fullfile(fullfile(folder,'H0'),'*.mat'));
    H0_files = arrayfun(@(x) fullfile(x.folder,x.name), H0_files, 'UniformOutput', false);
    files    = [files; H0_files];
end

