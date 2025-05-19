% bidsapp_Test
% Tests the behaviour of ERP_Core_WB.m
% called via bidsapp -- edit line 7 to ensure the path is correct
% run in command window from code folder as:
% results = runtests('bidsapp_Test'); table(results)

InputDataset = fileparts(pwd); % running from /work (understood as BIDS code) this should be correct

% set a bunch of options
tasks           = {'MMN','N400'};
Subjects        = {'sub-001','sub-002','sub-008','sub-010','sub-011','sub-022','sub-030','sub-031'};
high_pass       = 0.1;
ICAname         = 'runica';
epoch_window    = [-0.5 0.5];
baseline_window = [-500 -100];
analysis_window = [-100 500];
estimation      = 'OLS';
nboot           = 655;
tfce            = false;
OutputLocation  = [fileparts(InputDataset) filesep 'bidsapp_Test'];

% compute and assert
bidsapp(InputDataset,OutputLocation,'participant','TaskLabel',tasks,'SubjectLabel',...
    Subjects, 'high_pass',high_pass,'ICAname',ICAname,'epoch_window',epoch_window,...
    'baseline_window',baseline_window,'analysis_window',analysis_window);
% checks which subjects and tasks are present
subD = dir([OutputLocation filesep 'sub*']); 
assert(size(subD,1)==length(Subjects)-1,...
    sprintf('the number of subjects in derivatives %g does match was it expsted %g',...
    size(subD,1),length(Subjects)-1));
for t = 1:size(subD,1)
    taskD{t} = dir(fullfile(subD(t).folder,[subD(t).name])); taskD{t}(1:2) = [];
end
for t = 1:length(tasks)
    names{t} = cell2mat(unique(cellfun(@(x) x(t).name, taskD, 'UniformOutput', false)));
end
whichtasks = arrayfun(@(x) any(contains(x,tasks)),names);
assert(sum(whichtasks)==length(tasks),...
    sprintf('some tasks are missing: %s\n',tasks{whichtasks==0}))

% second level
Outputfolder = fullfile([OutputLocation filesep 'derivatives'],'group_level');
bidsapp(OutputLocation,Outputfolder,'group','nboot',nboot,'tfce',tfce)
whichfiles = dir([OutputLocation filesep 'derivatives' filesep 'group_level']); whichfiles(1:2) = []; 
assert(sum(arrayfun(@(x) any(contains(x.name,tasks(t))),whichfiles))==1,...
    sprintf('2nd level error, task %s missing',tasks{t}))

% ----------
% clean up
% ----------
rmdir(OutputLocation, 's')

