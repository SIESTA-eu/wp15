function bidsapp(varargin)

  % BIDSAPP is a wrapper for a MATLAB-based BIDS application.
  %
  % It is implemented for the MATLAB-based pipelines in SIESTA and follows
  % https://doi.org/10.1371/journal.pcbi.1005209. Each MATLAB-based pipeline should
  % have its own copy of this function, adapted to the specific requirements. The main
  % task of this wrapper is to parse the input arguments consistently and then to call
  % the actual code that implements the participant- or group-level analysis.
  %
  % Use as
  %   bidsapp [options] inputdir outputdir level
  %
  % The inputdir must be a directory containing a BIDS dataset.
  % The outputdir must be a directory that will contain the result.
  % The level must be 'participant' or 'group'.
  %
  % Supported options
  %   -h,--help         show this help and exit
  %   -v,--verbose      show more verbose information for debugging
  %   --version         show the version and exit
  %
  % See also INPUTPARSER, ARGUMENTS, FT_GETOPT

  % Copyright (C) 2024, Robert Oostenveld

  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  % parse the command-line options
  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  
  % the last three arguments must be inputdir, outputdir and level
  if nargin<3
    error('not enough input arguments')
  end

  inputdir  = varargin{end-2};
  outputdir = varargin{end-1};
  level     = varargin{end}; % participant or group

  % the last three arguments must be strings
  if ~isa(inputdir, 'char') && ~isa(inputdir, 'string')
    error('incorrect specification of inputdir');
  elseif ~isa(outputdir, 'char') && ~isa(outputdir, 'string')
    error('incorrect specification of inputdir');
  elseif ~isa(level, 'char') && ~isa(level, 'string')
    error('incorrect specification of inputdir');
  end

  if ~strcmpi(level, 'participant') && ~strcmpi(level, 'group')
    error('level should either be ''participant'' or ''group''');
  end

  if ~exist(inputdir, 'dir')
    disp(inputdir);
    error('input directory does not exist');
  end

  if ~exist(outputdir, 'dir')
    warning('creating output directory');
    [success, message] = mkdir(outputdir);
    if ~success
      error(message);
    end
  end

  % the last three arguments have been dealt with
  varargin = varargin(1:end-3);

  % store all options in a structure
  options.inputdir  = inputdir;
  options.outputdir = outputdir;
  options.level     = level;

  % optional arguments can be "flags" that come by themselves, like '-h' or '--help'
  % optional arguments can also have values, like '--species {human,rat}'

  % flags are represented as true/false
  options.version    = false;
  options.help       = false;
  options.verbose    = false;
  % other options each have their own value, either a string or a number
  % ...

  % deal with the additional stuff: FIXME all of this assumes that the last
  % 3 arguments in the list are the positional required ones
  while ~isempty(varargin)
    switch varargin{1}
      case {'--subject-label'}
        cnt = 1;
        options.subjectlist = cell(1,0);
        while cnt<numel(varargin) && ~(startsWith(varargin{cnt+1}, '-'))
          options.subjectlist{end+1} = sprintf('sub-%s', varargin{cnt+1});
          cnt = cnt+1;
        end
        varargin(1:cnt) = [];
      case {'--session-label'}
        cnt = 1;
        options.sessionlist = cell(1,0);
        while cnt<numel(varargin) && ~(startsWith(varargin{cnt+1}, '-'))
          options.sessionlist{end+1} = sprintf('ses-%s', varargin{cnt+1});
          cnt = cnt+1;
        end
        varargin(1:cnt) = [];
      case {'--version'}
        options.version = true;
        varargin(1) = [];
      case {'-h', '--help'}
        options.help = true;
        varargin(1) = [];
      case {'-v', '--verbose'}
        options.verbose = true;
        varargin(1) = [];
    end % switch
  end % while
  if ~isfield(options, 'subjectlist')
    options.subjectlist = 'all';
  end
  if ~isfield(options, 'sessionlist')
    options.sessionlist = 'all';
  end
  
  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  % call the actual code to execute the pipeline
  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

  % we want the help of the BIDS app to be shown, not the pipeline code
  if options.help
    help(mfilename);
    return
  end

  % Here the analysis pipeline specific MATLAB code is called, using the options
  % structure that was parsed above. The purpose of this "bidsapp" function and the
  % "workPackageCerCo" function is very similar and in principle they could be merged.

  run_pipeline(options.inputdir, options.outputdir, options.level, options.subjectlist, options.sessionlist);
end
