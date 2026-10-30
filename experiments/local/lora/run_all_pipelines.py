import os
import sys
import subprocess


def main():
    # If a folder is passed as an argument, we use it, otherwise we use the script folder
    if len(sys.argv) > 1:
        base_dir = os.path.abspath(sys.argv[1])
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"{'*'*60}")
    print(f" PIPELINE EXECUTION ON ALL SUB-FOLDERS")
    print(f" Base folder: {base_dir}")
    print(f"{'*'*60}")
    
    # Find all sub-folders that contain run_pipeline.py
    subfolders = sorted([
        d for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d))
        and not d.startswith("__")
        and os.path.exists(os.path.join(base_dir, d, "run_pipeline.py"))
    ])
    
    if not subfolders:
        print("\nNo sub-folder with run_pipeline.py found.")
        return
    
    print(f"\nFound {len(subfolders)} folders to process:")
    for i, name in enumerate(subfolders, 1):
        print(f"  {i}. {name}")
    
    successes = 0
    failures = 0
    
    for i, folder_name in enumerate(subfolders, 1):
        dir_path = os.path.join(base_dir, folder_name)
        
        print(f"\n{'='*60}")
        print(f" [{i}/{len(subfolders)}] PIPELINE START: {folder_name}")
        print(f"{'='*60}")
        
        # Executes run_pipeline.py in the sub-folder
        result = subprocess.run(
            [sys.executable, "run_pipeline.py"],
            cwd=dir_path
        )
        
        if result.returncode != 0:
            print(f"\n!!! ERROR in pipeline of: {folder_name}")
            failures += 1
        else:
            print(f"\n>>> SUCCESSFULLY COMPLETED: {folder_name}")
            successes += 1
    
    # Final summary
    print(f"\n{'*'*60}")
    print(f" GLOBAL EXECUTION SUMMARY")
    print(f"{'*'*60}")
    print(f"  Total folders processed: {len(subfolders)}")
    print(f"  Successes: {successes}")
    print(f"  Failures: {failures}")
    print(f"{'*'*60}")


if __name__ == "__main__":
    main()
