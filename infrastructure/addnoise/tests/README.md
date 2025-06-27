# Tests for addnoise

All tests have the noise in a TSV file as a single row, but differ in the format of the pipeline results files that are listed in the whitelist file.

Test 1 has pipeline results as a TSV file with a row vector.

Test 3 has pipeline results as a TSV file with a column vector.

Test 3 has pipeline results as a MAT file with a row vector.

Test 4 has pipeline results as a NII file with a 1x2x3 array.

Test 5 has pipeline results in three different MAT files.

Test 6 has pipeline results in two MAT files, both containing a structure, one in v6 and the other in v73 format.
