# Tests for mergegroup

Test 0 has scalar group-level results formatted as a TXT file.

Test 1 has scalar group-level results, formatted as a TSV file and different variations of a whitelist file.

Test 2 has group-level results as a row vector, formatted as a TSV file and different variations of a whitelist file.

Test 3 has group-level results as a column vector, formatted as a TSV file and different variations of a whitelist file.

Test 4 has group-level results as a 2x2 matrix, formatted as a TSV file and different variations of a whitelist file.

Test 5 has group-level results as a 2x2 matrix, formatted as a CSV file and different variations of a whitelist file.

Test 6 has group-level results as a 2x2 matrix, formatted as a CSV file with a header line, and different variations of a whitelist file.

Test 7 has group-level results as a NII file with an 1x2x3 array, and different variations of a whitelist file.

Test 8 has group-level results as a MAT file containing a single scalar.

Test 9 has group-level results as a MAT file containing two scalars and a structure.

Test 10 has group-level results as a MAT, NII and TSV file.

Test 11 is not for mergegroup itself, but for the MATLAB file reading. It has multiple MAT files in different formats (v4, v6, v7, v73) with different contents (array, structure, cell).
