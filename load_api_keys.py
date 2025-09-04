#!/usr/bin/env python3
"""
API Keys Loader Utility
Loads API keys from api_keys.yml and sets them as environment variables
"""

import os
import yaml
import sys
from pathlib import Path

def load_api_keys(config_file="api_keys.yml"):
    """
    Load API keys from YAML configuration file and set as environment variables
    
    Args:
        config_file (str): Path to the API keys configuration file
    
    Returns:
        dict: Dictionary of loaded API keys
    """
    config_path = Path(config_file)
    
    if not config_path.exists():
        print(f"Warning: {config_file} not found. Please create it with your API keys.")
        print(f"You can copy from api_keys.yml.template and fill in your actual keys.")
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not config:
            print(f"Warning: {config_file} is empty or invalid.")
            return {}
        
        # Set environment variables
        for key, value in config.items():
            if isinstance(value, str) and value.strip():
                os.environ[key] = value
                print(f"Loaded API key: {key}")
        
        return config
    
    except yaml.YAMLError as e:
        print(f"Error parsing {config_file}: {e}")
        return {}
    except Exception as e:
        print(f"Error loading {config_file}: {e}")
        return {}

def main():
    """Main function to load API keys when run as script"""
    script_dir = Path(__file__).parent
    config_file = script_dir / "api_keys.yml"
    
    print("Loading API keys...")
    keys = load_api_keys(config_file)
    
    if keys:
        print(f"Successfully loaded {len(keys)} API keys.")
    else:
        print("No API keys loaded.")
        sys.exit(1)

if __name__ == "__main__":
    main()