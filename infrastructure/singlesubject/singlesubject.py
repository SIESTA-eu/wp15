import os, shutil, sys
import pandas as pd

def singlesubject_(input_dir, output_dir ,participant_nr):

    try:
        fl_dir = [dirs for root, dirs, _ in os.walk(input_dir)]
        if participant_nr not in fl_dir[0]:
            print(f"Error: participant_nr[{participant_nr}] does not exist in {input_dir}.")
            pass   
        else:         
            output_base = os.path.join(os.getcwd(), f"{output_dir}_{participant_nr[4:]}")
            for root, dirs, files in os.walk(input_dir):
                rel_path = os.path.relpath(root, input_dir)
                output_path = os.path.join(output_base, rel_path)
                os.makedirs(output_path, exist_ok=True)
                for file in files:
                    if file.endswith('.tsv'):
                        try:
                            df = pd.read_csv(os.path.join(root, file), sep='\t')
                            if participant_nr in df['participant_id'].values:
                                row = df[df['participant_id'] == participant_nr]
                                row.to_csv(os.path.join(output_path, file), sep='\t', index=False)
                        except:
                            print("Error: participant_nr {participant_nr} not found in the file: {os.path.join(root, file)}")
                    if not file.endswith('.tsv'):
                        try:
                            shutil.copy2(os.path.join(root, file), output_path)
                        except FileExistsError:
                            pass
                    #elif any(str(participant_nr) in file for file in files):
                    #    try:
                    #        shutil.copy2(os.path.join(root, file), output_path)
                    #    except FileExistsError:
                    #        pass
		        
                for dir in dirs:
                    if dir == participant_nr:
                        src_dir = os.path.join(root, dir)
                        dst_dir = os.path.join(output_path, dir)
                        try:
                            shutil.copytree(src_dir, dst_dir)
                        except FileExistsError:
                            pass 
		        
                for root, dirs, files in os.walk(output_base, topdown=False):
                    for dir in dirs:
                        dir_path = os.path.join(root, dir)
                        if str(participant_nr[:4]) in dir_path and str(participant_nr) not in dir_path:
                            try:
                                shutil.rmtree(dir_path)
                            except OSError as e:
                                print("Error: to investigate")
                                pass
            print(f"{participant_nr} has been succesfully processed.")        
        return True
    except FileNotFoundError:
        print("Error: Input folder Not Found. Please make sure of input folder name.", file=sys.stderr)
        return False

def main():
    if len(sys.argv) < 4:
        print("Usage: apptainer run singlesubject.sif <inputdir> <outputdir> <participant_nr>")
        sys.exit(1)
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    participant_nr = sys.argv[3]
    pid = singlesubject_(input_dir, output_dir,participant_nr)
    if not pid:
        print("Nothing to return!")
        sys.exit(1)

if __name__ == "__main__":
    main()
