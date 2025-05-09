function hello(varargin)
    disp('Hello from octave pipeline!');
    if nargin > 0
        disp(['Arguments reçus : ', strjoin(varargin, ', ')]);
    end
