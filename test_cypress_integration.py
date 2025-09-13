#!/usr/bin/env python3
"""
Test script to verify Cypress integration with Bilibili dynamic fetching
"""

import os
import sys
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from common.cypress_runner import CypressRunner
from common.logger import log

def test_cypress_runner():
    """Test the CypressRunner functionality"""
    log.info("Starting Cypress integration test...")
    
    # Initialize CypressRunner
    cypress_runner = CypressRunner()
    
    # Test UID (the one from your example)
    test_uid = "322005137"
    
    try:
        # Test if Cypress can be installed/is available
        log.info("Checking Cypress installation...")
        if not cypress_runner.ensure_cypress_installed():
            log.error("Failed to ensure Cypress is installed")
            return False
        
        log.info("Cypress installation check passed")
        
        # Try to extract Bilibili dynamic data
        log.info(f"Attempting to extract dynamic data for UID: {test_uid}")
        result = cypress_runner.run_bilibili_dynamic_extraction(test_uid, timeout=120)
        
        if result is None:
            log.error("Failed to extract data - result is None")
            return False
        
        log.info(f"Extraction result: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result.get('success'):
            log.info("✅ Cypress extraction successful!")
            data = result.get('data', {})
            if data.get('code') == 0:
                items = data.get('data', {}).get('items', [])
                log.info(f"Found {len(items)} dynamic items")
                if items:
                    first_item = items[0]
                    log.info(f"First item ID: {first_item.get('id_str')}")
                    log.info(f"Author: {first_item.get('modules', {}).get('module_author', {}).get('name')}")
                return True
            else:
                log.error(f"API returned error code: {data.get('code')} - {data.get('message')}")
                return False
        else:
            log.error(f"Extraction failed: {result.get('error')}")
            return False
            
    except Exception as e:
        log.error(f"Test failed with exception: {e}", exc_info=True)
        return False

def test_query_bilibili_integration():
    """Test the QueryBilibili class with Cypress enabled"""
    log.info("Testing QueryBilibili integration...")
    
    try:
        from query_task.query_bilibili import QueryBilibili
        
        # Create a test configuration with Cypress enabled
        test_config = {
            "enable": True,
            "name": "cypress_test",
            "uid_list": ["322005137"],
            "use_cypress": True,
            "enable_dynamic_check": True,
            "enable_living_check": False,
            "begin_time": "00:00",
            "end_time": "23:59",
            "len_of_deque": 5,
            "skip_forward": True
        }
        
        # Initialize QueryBilibili with Cypress
        query_bili = QueryBilibili(test_config)
        
        if query_bili.cypress_runner is None:
            log.error("CypressRunner not initialized properly")
            return False
        
        log.info("QueryBilibili initialized with Cypress support")
        
        # Test the Cypress query method directly
        test_uid = "322005137"
        log.info(f"Testing Cypress query for UID: {test_uid}")
        
        query_bili.query_dynamic_cypress(test_uid)
        log.info("Cypress query method completed")
        
        return True
        
    except Exception as e:
        log.error(f"QueryBilibili integration test failed: {e}", exc_info=True)
        return False

def main():
    """Main test function"""
    log.info("=" * 50)
    log.info("CYPRESS INTEGRATION TEST")
    log.info("=" * 50)
    
    # Test 1: Basic Cypress functionality
    log.info("\n🧪 Test 1: Basic Cypress Runner")
    test1_result = test_cypress_runner()
    
    # Test 2: QueryBilibili integration
    log.info("\n🧪 Test 2: QueryBilibili Integration")
    test2_result = test_query_bilibili_integration()
    
    # Summary
    log.info("\n" + "=" * 50)
    log.info("TEST SUMMARY")
    log.info("=" * 50)
    log.info(f"Cypress Runner Test: {'✅ PASSED' if test1_result else '❌ FAILED'}")
    log.info(f"QueryBilibili Integration: {'✅ PASSED' if test2_result else '❌ FAILED'}")
    
    if test1_result and test2_result:
        log.info("\n🎉 All tests passed! Cypress integration is working.")
        return True
    else:
        log.error("\n💥 Some tests failed. Please check the logs above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
