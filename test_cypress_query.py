#!/usr/bin/env python3
"""
Test script for query_dynamic_cypress functionality
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common.logger import log
from query_task.query_bilibili import QueryBilibili

def test_cypress_query():
    """
    Test the query_dynamic_cypress method with a real Bilibili UID
    """
    log.info("=" * 60)
    log.info("Testing query_dynamic_cypress functionality")
    log.info("=" * 60)
    
    # Create a test configuration with Cypress enabled
    test_config = {
        "name": "test_cypress_bilibili",
        "enable": True,
        "type": "bilibili",
        "intervals_second": 60,
        "begin_time": "00:00",
        "end_time": "23:59",
        "target_push_name_list": [],  # No push channels for testing
        "enable_dynamic_check": True,
        "enable_living_check": False,
        "uid_list": ["322005137"],  # Test UID
        "skip_forward": False,
        "cookie": "",
        "payload": "",
        "use_cypress": True  # Enable Cypress functionality
    }
    
    try:
        # Initialize QueryBilibili with Cypress enabled
        log.info("Initializing QueryBilibili with Cypress support...")
        query_bili = QueryBilibili(test_config)
        
        if query_bili.cypress_runner is None:
            log.error("Cypress runner is not initialized!")
            return False
        
        log.info("✅ QueryBilibili initialized successfully with Cypress support")
        
        # Test UID
        test_uid = "322005137"
        log.info(f"Testing Cypress query for UID: {test_uid}")
        
        # Run the cypress query
        log.info("🚀 Starting Cypress dynamic extraction...")
        query_bili.query_dynamic_cypress(test_uid)
        
        log.info("✅ Cypress query completed")
        
        # Check if any fixture files were generated
        fixtures_dir = query_bili.cypress_runner.fixtures_dir
        log.info(f"Checking fixtures directory: {fixtures_dir}")
        
        if fixtures_dir.exists():
            fixture_files = list(fixtures_dir.glob(f"*{test_uid}*.json"))
            if fixture_files:
                log.info(f"✅ Found {len(fixture_files)} fixture files:")
                for file in fixture_files:
                    log.info(f"  - {file.name}")
            else:
                log.warning("⚠️  No fixture files found for this UID")
        else:
            log.warning("⚠️  Fixtures directory does not exist")
        
        return True
        
    except Exception as e:
        log.error(f"❌ Test failed with error: {e}", exc_info=True)
        return False

def main():
    """Main test function"""
    log.info("Starting Cypress query test...")
    
    success = test_cypress_query()
    
    if success:
        log.info("🎉 Test completed successfully!")
    else:
        log.error("💥 Test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
