import os
import sys
import subprocess

def run_script_in_dir(script_name, dir_path):
    if not os.path.exists(dir_path):
        print(f"Folder not found: {dir_path}")
        return False
    
    script_path = os.path.join(dir_path, script_name)
    if not os.path.exists(script_path):
        print(f"Script not found: {script_path}")
        return False
        
    print(f"\n---> Executing {script_name} in folder {os.path.basename(dir_path)}...")
    
    # Executes the script setting the working directory to dir_path (as if the user had entered it from the terminal)
    result = subprocess.run([sys.executable, script_name], cwd=dir_path)
    
    if result.returncode != 0:
        print(f"!!! Error executing {script_name} in {dir_path}")
        return False
    return True

def main():
    # Resolve the default folder from this script, independent of the working directory.
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
    base_dir = os.path.abspath(base_dir)
    print(f"Pipeline start on base folder: {base_dir}")
    
    # Find all subfolders in the base folder
    subdirs = [os.path.join(base_dir, d) for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    
    if not subdirs:
        print("No subfolders found.")
        return
        
    for subdir in subdirs:
        # If there is a folder called __pycache__ or similar, we skip it
        if os.path.basename(subdir).startswith("__"):
            continue
            
        print(f"\n{'='*60}")
        print(f" STARTING FOLD PROCESSING: {os.path.basename(subdir)}")
        print(f"{'='*60}")
        
        # 1. Run train.py in train/
        train_dir = os.path.join(subdir, "train")
        if not run_script_in_dir("train.py", train_dir):
            print(f"Pipeline interrupted for {os.path.basename(subdir)}.")
            continue
            
        # 2. Run run_inference.py in tester/
        tester_dir = os.path.join(subdir, "tester")
        if not run_script_in_dir("run_inference.py", tester_dir):
            print(f"Pipeline interrupted for {os.path.basename(subdir)}.")
            continue
            
        
        print(f"\n>>> Successfully completed for: {os.path.basename(subdir)}")
        
    print(f"\n{'*'*60}\nGLOBAL PIPELINE TERMINATED\n{'*'*60}")

if __name__ == "__main__":
    main()
