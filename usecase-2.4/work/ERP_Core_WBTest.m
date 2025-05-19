% Test the behaviour of ERP_Core_WB.m
% edit/make sure the path line 7 is correct
% edit line 8 to keep default results
% run in command window from code folder as:
% results = runtests('ERP_Core_WBTest'); table(results)

dataset_folder = fileparts(pwd); % running from /work this should be correct
keep_default_results = 'True'; % ie outputs from Test 1

%% Test 1a - Run 1st level with Defaults (only dataset_folder specified)
out = ERP_Core_WB(dataset_folder,[],1);
assert(out.AnalysisLevel==1,'Analysis Level 1 not started')

%% Test 1b - 1st level tasks are all present 
tasks = {'ERN','MMN','N170','N2pc','N400','P3'};
assert(all(isfield(out,tasks)),sprintf('1st level task %s is missing ',tasks{~isfield(out,tasks)}))

%% Test 1c - expected N participants are present in each task
tasksN = [38 38 37 38 38 36]; % as per ERP_Core_WB line 335+
for t = 1:length(tasks)
    assert(length(out.(tasks{t}).participant)>=36,...
        sprintf('%g subject(s) absent from task %s', ...
        tasksN(t)-length(out.(tasks{t}).participant),tasks{t}))
end

%% Test 1d - 1st level GLM has the right number of outputs
GLMN = [9 7 9 9 9 9]; % 7 by default + 2 contrasts
for t = 1:length(tasks)
    observedN = sum(cellfun(@(x) size(x.glm_files,1)==GLMN(t), out.(tasks{t}).participant));
    assert(observedN==tasksN(t), sprintf('%g subject(s) not processed in task %s', ...
        tasksN(t)-observedN))
end

%% Test 1e: 2nd level analysis with defaults (only [dataset_folder filesep 'derivatives'] as input specified)
out = ERP_Core_WB([dataset_folder filesep 'derivatives'],[],2);
assert(out.AnalysisLevel==2,'Analysis Level 2 not started')

%% Test 1f: 2nd level tasks are all present 
assert(all(isfield(out,tasks)),sprintf('2nd level task %s is missing ',tasks{~isfield(out,tasks)}))
clear tasks tasksN GLMN

% ----------
% clean up
% ----------
if ~istrue(keep_default_results)
    rmdir([dataset_folder filesep 'derivatives'], 's')
end

%% Test 2a: run 2nd level with a specified OutputLocation and tasks
OutputLocation = [fileparts(dataset_folder) filesep 'ERP_CoreTest2'];
tasks          = {'MMN','N400'};
out = ERP_Core_WB([dataset_folder filesep 'derivatives'],OutputLocation,2,'TaskLabel',tasks);
assert(out.AnalysisLevel==2,'Analysis Level 2 not started')

%% Test 2b: 2nd level tasks are present 
assert(all(isfield(out,tasks)),sprintf('2nd level task %s is missing ',tasks{~isfield(out,tasks)}))

% ----------
% clean up
% ----------
rmdir(OutputLocation, 's')

%% Test 3a - run 1st level run dataset_folder, OutputLocation, tasklist and sublist
OutputLocation = [fileparts(dataset_folder) filesep 'ERP_CoreTest3'];
SubjectLabels  = {'sub-001','sub-002','sub-008','sub-010','sub-011','sub-022','sub-030','sub-031'};
out = ERP_Core_WB(dataset_folder,OutputLocation,1,'TaskLabel',tasks,'SubjectLabel',SubjectLabels);
assert(out.AnalysisLevel==1,'Analysis Level 1 not started')

%% Test 3b - are the requested task present 
assert(length(fieldnames(out))==3,sprintf('2 tasks specified but %g fields found',length(fieldnames(out))-1))
assert(all(isfield(out,tasks)),sprintf('1st level task %s is missing although specified as input',tasks{~isfield(out,tasks)}))

%% Test 3c - are the N participants requested present
for t = 1:length(tasks)
    test = any([length(out.(tasks{t}).participant)==length(SubjectLabels)-1, ...
        length(out.(tasks{t}).participant)==length(SubjectLabels)]);
    assert(test,sprintf('%g subject(s) absent from task %s', ...
        length(SubjectLabels)-length(out.(tasks{t}).participant),tasks{t}))
end
clear tasks SubjectLabels

%% Test 4 - 2nd level from 1st level output for one task (+nboot and tfce parameter changed)
derivatives_folder = fullfile(OutputLocation,['N400' filesep 'derivatives']);
out = ERP_Core_WB(derivatives_folder ,[],2,'TaskLabel',{'N400'},'nboot',699,'tfce',0);
assert(out.AnalysisLevel==2,'Analysis Level 2 not started')
assert(isfield(out,'N400'),'2nd level 1 task folder input (N400) fails')

% ----------
% clean up
% ----------
rmdir(OutputLocation, 's')

%% Test 5 - can 1st level run changing 1st level parameters
tasks           = {'ERN','N2pc'};
high_pass       = 0.1;
ICAname         = 'runica';
epoch_window    = [-0.5 0.5];
baseline_window = [-500 -100];
analysis_window = [-100 500];
estimation      = 'OLS';
OutputLocation  = [fileparts(dataset_folder) filesep 'ERP_CoreTest5'];
out = ERP_Core_WB(dataset_folder,OutputLocation,1,'TaskLabel',tasks,...
    'high_pass',high_pass,'ICAname',ICAname,'epoch_window',epoch_window,...
    'baseline_window',baseline_window,'analysis_window',analysis_window);
assert(out.AnalysisLevel==1,'Analysis Level 1 not started')
assert(all(isfield(out,tasks)),sprintf('1st level task %s is missing ',tasks{~isfield(out,tasks)}))
tasksN = [38 39]; % as per ERP_Core_WB line 380+
for t = 1:length(tasks)
    assert(length(out.(tasks{t}).participant)==tasksN(t),...
        sprintf('%g subject(s) absent from task %s', ...
        tasksN(t)-length(out.(tasks{t}).participant),tasks{t}))
end
GLMN = [9 9]; % 7 by default + 2 contrasts
for t = 1:length(tasks)
    observedN = sum(cellfun(@(x) size(x.glm_files,1)==GLMN(t), out.(tasks{t}).participant));
    assert(observedN==tasksN(t), sprintf('%g subject(s) not processed in task %s', ...
        tasksN(t)-observedN))
end


% ----------
% clean up
% ----------
rmdir(OutputLocation, 's')

