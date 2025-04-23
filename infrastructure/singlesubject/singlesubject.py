import os, shutil, sys, re
import pandas as pd

def singlesubject_(input_dir, output_dir, participant_id):

    try:
        participant_ids = sorted([item for item in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, item)) and item.startswith("sub-")])
        if participant_id in participant_ids:
            # the participant_id was specified as a string
            pass
        elif participant_id not in participant_ids and int(participant_id):
            # the participant_id was specified as a positive number
            participant_id = participant_ids[int(participant_id) - 1]

        if participant_id in participant_ids:
            skip_ids = [id for id in participant_ids if id != participant_id]

            output_base = os.path.join(os.getcwd(), f"{output_dir}")
            for root, dirs, files in os.walk(input_dir):
                if len(set(root.split(os.sep)) & set(skip_ids)) > 0:
                    # skip any directories that contain another participant ID
                    continue

                rel_path = os.path.relpath(root, input_dir)
                output_path = os.path.join(output_base, rel_path)
                os.makedirs(output_path, exist_ok=True)
                for file in files:
                    if file.endswith('.tsv'):
                        try:
                            df = pd.read_csv(os.path.join(root, file), sep='\t')
                            try:
                                if participant_id in df[list(df.columns)[0]].values:
                                    row = df[df[list(df.columns)[0]] == participant_id]
                                    row.to_csv(os.path.join(output_path, file), sep='\t', index=False)
                            except Exception as e:
                                print(e)
                                pass
                        except:
                            print("Error: {participant_id} not found in the file: {os.path.join(root, file)}")
                    if not file.endswith('.tsv'):
                        try:
                            shutil.copy2(os.path.join(root, file), output_path)
                        except FileExistsError:
                            pass

                for dir in dirs:
                    if dir == participant_id:
                        src_dir = os.path.join(root, dir)
                        dst_dir = os.path.join(output_path, dir)
                        try:
                            shutil.copytree(src_dir, dst_dir)
                        except FileExistsError:
                            pass 
        	    
                for root, dirs, files in os.walk(output_base, topdown=False):
                    for dir in dirs:
                        dir_path = os.path.join(root, dir)
                        if str(participant_id[:4]) in dir_path and str(participant_id) not in dir_path:
                            try:
                                shutil.rmtree(dir_path)
                            except OSError as e:
                                print("Error: {e}")
                                pass
            print(f"{participant_id} has been successfully split to {str(output_dir)}")        
        else:
            print(f"Error: the participant {participant_id} does not exist in {input_dir}.")  
        return True
    except FileNotFoundError:
        print("Error: Input folder Not Found. Please make sure of input folder name.", file=sys.stderr)
        return False

def main(args=None):
    if args is None:
        args = sys.argv
    if len(args) < 4:
        print("Usage: singlesubject.py <inputdir> <outputdir> <participant_nr>")
        sys.exit(1)
    input_dir = args[1]
    output_dir = args[2]
    participant_id = args[3] # this can be either a positive number or the participant ID itself
    pid = singlesubject_(input_dir, output_dir, participant_id)
    
    if not pid:
        print("Nothing to return!")
        sys.exit(1)

if __name__ == "__main__":
    main()
