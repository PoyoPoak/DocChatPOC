import os
import sys
from dotenv import load_dotenv

load_dotenv()
config = {
    "WORKING_DIR": os.getenv("WORKING_DIR")
}

setup_dir = os.path.join(config['WORKING_DIR'], 'setup')
if setup_dir not in sys.path:
    sys.path.insert(0, setup_dir)

import crawler
import processor
import upload

def run_module(module, name):
    if hasattr(module, 'main'):
        module.main() 
    else:
        print(f"No main() function found in the {name} module.")

if __name__ == "__main__":
    run_module(crawler, 'crawler')
    run_module(processor, 'processor')
    run_module(upload, 'upload')
    
    print("All modules executed successfully.")
