function unzipMRIs(path_input)
    list_fmris = dir(fullfile(path_input, 'sub*nii.gz'));

    if ~isempty(list_fmris)
        for f = 1:numel(list_fmris)
            fname = fullfile(list_fmris(f).folder, list_fmris(f).name);
            fprintf('unzipping %s', fname)
            gunzip(fname);
            delete(fname);
        end
    end
end