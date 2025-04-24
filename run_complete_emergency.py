#!/usr/bin/env python3
"""
Simple script to run the standalone emergency login system.
This bypasses the main application entirely to avoid CSRF issues.
"""
import os
import sys
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_standalone_system():
    """Run the standalone emergency login system on a different port."""
    try:
        # Execute the standalone emergency login script
        cmd = [sys.executable, 'complete_emergency.py']
        
        # Start the process
        logger.info(f"Starting standalone emergency login system...")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Log the process output
        logger.info(f"Standalone system started with PID: {process.pid}")
        logger.info(f"Visit http://0.0.0.0:5001/complete-emergency/login to access the emergency login system")
        
        try:
            # Stream output
            for line in process.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
            
            # Wait for the process to complete
            process.wait()
            
            if process.returncode != 0:
                logger.error(f"Standalone system exited with error code: {process.returncode}")
            else:
                logger.info("Standalone system exited normally")
        except KeyboardInterrupt:
            logger.info("Shutting down standalone system...")
            process.terminate()
            process.wait()
            logger.info("Standalone system shut down")
    except Exception as e:
        logger.error(f"Error running standalone system: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(run_standalone_system())