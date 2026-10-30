"""Run dataset builders below this experiment directory."""
import os
import subprocess
import sys

BUILDER_PREFIXES = ("build_test_dataset", "build_training_dataset")


def main():
    base_dir = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    if not os.path.isdir(base_dir):
        raise FileNotFoundError(f"Experiment folder not found: {base_dir}")
    for directory, subfolders, filenames in os.walk(base_dir):
        subfolders[:] = sorted(name for name in subfolders if not name.startswith((".", "__")))
        for filename in sorted(filenames):
            if filename.endswith(".py") and filename.startswith(BUILDER_PREFIXES):
                print(f"Building dataset with {os.path.join(directory, filename)}")
                subprocess.run([sys.executable, filename], cwd=directory, check=True)


if __name__ == "__main__":
    main()
