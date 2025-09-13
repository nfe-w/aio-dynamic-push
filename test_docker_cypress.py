#!/usr/bin/env python3
"""
Test script for Cypress functionality in Docker environment
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common.logger import log
from query_task.query_bilibili import QueryBilibili

def test_cypress_in_docker():
    """
    Test the query_dynamic_cypress method in Docker environment
    """
    log.info("=" * 60)
    log.info("Testing Cypress functionality in Docker")
    log.info("=" * 60)
    
    # Check if we're running in Docker
    if os.path.exists('/.dockerenv'):
        log.info("✅ Running inside Docker container")
    else:
        log.info("⚠️  Not running in Docker container")
    
    # Check Node.js and npm availability
    try:
        import subprocess
        node_version = subprocess.check_output(['node', '--version'], text=True).strip()
        npm_version = subprocess.check_output(['npm', '--version'], text=True).strip()
        log.info(f"✅ Node.js version: {node_version}")
        log.info(f"✅ npm version: {npm_version}")
    except Exception as e:
        log.error(f"❌ Node.js/npm not available: {e}")
        return False
    
    # Start Xvfb for headless display
    try:
        log.info("Starting Xvfb virtual display...")
        xvfb_process = subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1024x768x24'], 
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Give Xvfb time to start
        import time
        time.sleep(2)
        log.info("✅ Xvfb started successfully")
    except Exception as e:
        log.error(f"❌ Failed to start Xvfb: {e}")
        return False
    
    # Check Cypress installation with display available
    try:
        cypress_version = subprocess.check_output(['npx', 'cypress', '--version'], text=True).strip()
        log.info(f"✅ Cypress installed: {cypress_version}")
        
        # Verify Cypress can start
        log.info("Verifying Cypress installation...")
        subprocess.check_output(['npx', 'cypress', 'verify'], text=True)
        log.info("✅ Cypress verification successful")
    except Exception as e:
        log.error(f"❌ Cypress not available: {e}")
        # Try to stop Xvfb before returning
        try:
            xvfb_process.terminate()
        except:
            pass
        return False
    
    # Create a test configuration with Cypress enabled
    test_config = {
        "name": "docker_cypress_test",
        "enable": True,
        "type": "bilibili",
        "intervals_second": 60,
        "begin_time": "00:00",
        "end_time": "23:59",
        "target_push_name_list": [],
        "enable_dynamic_check": True,
        "enable_living_check": False,
        "uid_list": ["322005137"],
        "skip_forward": False,
        "cookie": "",
        "payload": "",
        "use_cypress": True
    }
    
    try:
        log.info("Initializing QueryBilibili with Cypress support...")
        query_bili = QueryBilibili(test_config)
        
        if query_bili.cypress_runner is None:
            log.error("❌ Cypress runner is not initialized!")
            return False
        
        log.info("✅ QueryBilibili initialized successfully")
        
        # Test UID
        test_uid = "322005137"
        log.info(f"Testing Cypress query for UID: {test_uid}")
        
        # Set DISPLAY for headless mode in Docker
        os.environ['DISPLAY'] = ':99'
        
        # Run the cypress query
        log.info("🚀 Starting Cypress dynamic extraction in Docker...")
        query_bili.query_dynamic_cypress(test_uid)
        
        log.info("✅ Cypress query completed in Docker")
        
        return True
        
    except Exception as e:
        log.error(f"❌ Docker test failed: {e}", exc_info=True)
        return False

def main():
    """Main test function"""
    log.info("Starting Docker Cypress test...")
    
    success = test_cypress_in_docker()
    
    if success:
        log.info("🎉 Docker Cypress test completed successfully!")
    else:
        log.error("💥 Docker Cypress test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
