function localizer = extractEvents(filename)

    localizer = '';

    check_nifti = endsWith(filename, '.nii');
    check_mat = endsWith(filename, '.mat');
    check_txt = endsWith(filename, '.txt');
    check_tsv = endsWith(filename, '.tsv');

    start_pos = strfind(filename, 'task');                

    if check_nifti == true || check_mat == true || check_txt == true
        final_pos = strfind(filename, 'bold');
    end 

    if check_tsv == true
        final_pos = strfind(filename, 'events');
    end 

    real_begin = start_pos + 5;
    real_end = final_pos - 2;
                                            
    %for r = real_begin:real_end
        %localizer = append(localizer, filename(r));
    %end

    % Extraction du segment du nom du fichier (utilisation de l'opérateur + pour les chaînes de caractères modernes)
    for r = real_begin:real_end
        localizer = [localizer,filename(r)]; % Utilisation de l'opérateur + pour les chaînes modernes
    end
end