function deleteVOE(path_input)

    list_subjects = dir(path_input);
    szSubjects = numel(list_subjects);

    for sub = 3:szSubjects
        check_sub = startsWith(list_subjects(sub).name, 'sub');

        if check_sub == true
            path_subject = fullfile(path_input, list_subjects(sub).name);
            path_func = fullfile(path_subject, 'func');
            list_files = dir(path_func);
            szFiles = size(list_files);
            
            for f = 3:szFiles(1)
                check_voe = contains(list_files(f).name, 'VOE');
                if check_voe == true
                    path_file = fullfile(path_func, list_files(f).name);
                    delete(path_file);
                end
            end
        end
    end
end 