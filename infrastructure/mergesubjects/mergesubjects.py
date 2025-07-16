import os, shutil, sys
import pandas as pd

def mergesubjects(inputs, output):
    try:
        os.makedirs(output, exist_ok=True)
    except Exception as e:
        print(f"Error creating output directory: {e}")
        return

    tsv = list()
    for input_dir in inputs:
        print(f"Merging {input_dir} ==> {output}")
        try:
            if not os.path.isdir(input_dir):
                raise ValueError(f"Input directory does not exist: {input_dir}")
        except Exception as e:
            print(f"Error validating input directory: {e}")
            continue

        tsv_aux = list()
        try:
            for root, dirs, files in os.walk(input_dir):
                try:
                    os.makedirs(output+"/"+"/".join(root.split("/")[1:]), exist_ok=True)
                except Exception as e:
                    print(f"Error creating subdirectory: {e}")
                    continue

                for file in files:
                    try:
                        if ".tsv" in file:
                            tsv_aux.append(os.path.join(root, file))
                        else: 
                            try:
                                shutil.copy2(os.path.join(root, file),
                                         output+"/"+"/".join(os.path.join(root, file).split("/")[1:]))
                            except FileExistsError:
                                pass
                            except Exception as e:
                                print(f"Error copying file {file}: {e}")
                    except Exception as e:
                        print(f"Error processing file {file}: {e}")
        except Exception as e:
            print(f"Error walking through directory {input_dir}: {e}")
            continue

        tsv.append(tsv_aux)

    try:
        if not tsv or not any(tsv):
            raise ValueError("No TSV files found to merge")
        
        for i in range(len(tsv[0])):
            try:
                file_name = [tsv[j][i].split("/")[-1] for j in range(len(tsv))][0]
                output_path = [output+"/"+"/".join(tsv[j][i].split("/")[1:-1]) for j in range(len(tsv))][0]
                try:
                    merged_df = pd.concat([pd.read_csv(tsv[j][i], sep='\t') for j in range(len(tsv))])
                    try:
                        merged_df.to_csv(output_path+"/"+file_name, sep='\t', index=False)
                    except Exception as e:
                        print(f"Error saving merged TSV {file_name}: {e}")
                except Exception as e:
                    print(f"Error reading or concatenating TSV files: {e}")
            except Exception as e:
                print(f"Error processing TSV file at index {i}: {e}")
    except Exception as e:
        print(f"Error during TSV merging process: {e}")

def main():
    try:
        if len(sys.argv) < 3:
            raise ValueError("Insufficient arguments")
    except Exception as e:
        print(f"Error: {e}")
        print("Usage: mergesubjects.py <inputdir1> <inputdir2> ... <inputdirN> <outputdir>")
        sys.exit(1)

    try:
        input_dirs = sys.argv[1:-1]
        output_dir = sys.argv[-1]
        mergesubjects(input_dirs, output_dir)
        print(f"All subjects has been successfully merged into output directory: {output_dir}")
    except Exception as e:
        print(f"Unexpected error in main execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
