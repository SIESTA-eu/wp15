% create output architecture directory based on input directory
function createDataStructure(path_input, path_output)

list_patients = dir(fullfile(path_input, 'sub*')); % in BIDS, all subjects start with 'sub'
sz = size(list_patients);

for p = 1:sz(1)
  path_subject = fullfile(path_input, list_patients(p).name);
  check_sub = startsWith(list_patients(p).name, 'sub');
  check_folder = isfolder(path_subject);

  if check_folder == true && check_sub == true
    pathSub_output = fullfile(path_output, list_patients(p).name);
    checkSub_output = isfolder(pathSub_output);

    if checkSub_output == false
      mkdir(pathSub_output);
    end

    path_func = fullfile(path_subject, 'func');

    list_niftis = dir(path_func);
    szNiftis = size(list_niftis);

    for n = 3:szNiftis(1)
      check_nifti = endsWith(list_niftis(n).name, 'nii');

      if check_nifti == true
        index = 1;
        start_pos = 0;
        final_pos = 0;
        filename = list_niftis(n).name;
        start_pos = strfind(list_niftis(n).name, 'task');
        final_pos = '';

        real_begin = -1;
        real_end = -1;

        final_pos = strfind(list_niftis(n).name, 'bold');
        real_begin = start_pos + 5;
        filename = list_niftis(n).name;
        real_end = final_pos - 2;

        localizer = '';

        for r = real_begin:real_end
          localizer = append(localizer, filename(r));
        end

        path_run = fullfile(pathSub_output, localizer);
        check_run = isfolder(path_run);

        if check_run == false
          mkdir(path_run);
        end
      end
    end
  end
end
