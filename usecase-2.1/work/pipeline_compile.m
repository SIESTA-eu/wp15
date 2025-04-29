% pipeline_compile uses the matlab compiler to create a compiled executable
% to run the matlab-version of the pipeline

result = compiler.build.standaloneApplication('pipeline.m');
system('mv pipelinestandaloneApplication pipeline_compiled');

% NOTE:
% janmathijs ran the above on the DCCN's filesystem, running matlab version
% 2024b. thus, in order to run the deployed application the MCR/R2024b
% needs to be installed within the pipeline container. Once upon a time
% these MCRs were relatively small, the one for R2024b is ~10GB large...

% the above uses the simplest way to create the compiled binary
