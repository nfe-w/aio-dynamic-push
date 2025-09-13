import json
import os
import subprocess
import time
import glob
from typing import Dict, Any, Optional
from pathlib import Path

from common.logger import log


class CypressRunner:
    """
    Utility class to run Cypress tests and extract data from Bilibili
    """
    
    def __init__(self, project_root: str = None):
        if project_root is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.project_root = Path(project_root)
        self.cypress_dir = self.project_root / "cypress"
        self.fixtures_dir = self.cypress_dir / "fixtures"
        
    def ensure_cypress_installed(self) -> bool:
        """
        Check if Cypress is installed and install if necessary
        """
        try:
            # Check if node_modules exists
            node_modules = self.project_root / "node_modules"
            if not node_modules.exists():
                log.info("Installing Cypress dependencies...")
                result = subprocess.run(
                    ["npm", "install"], 
                    cwd=self.project_root, 
                    capture_output=True, 
                    text=True,
                    timeout=300
                )
                if result.returncode != 0:
                    log.error(f"Failed to install dependencies: {result.stderr}")
                    return False
                log.info("Cypress dependencies installed successfully")
            
            return True
        except Exception as e:
            log.error(f"Error checking/installing Cypress: {e}")
            return False
    
    def run_bilibili_dynamic_extraction(self, uid: str, timeout: int = 60) -> Optional[Dict[str, Any]]:
        """
        Run Cypress test to extract Bilibili dynamic data
        
        Args:
            uid: Bilibili user ID
            timeout: Timeout in seconds
            
        Returns:
            Dictionary containing the extracted data or None if failed
        """
        if not self.ensure_cypress_installed():
            return None
            
        try:
            # Clear old fixture files for this UID
            self._cleanup_old_fixtures(uid)
            
            # Set environment variable for the UID
            env = os.environ.copy()
            env['CYPRESS_BILIBILI_UID'] = uid
            # Ensure headless mode environment variables
            env['DISPLAY'] = env.get('DISPLAY', ':99')
            env['ELECTRON_DISABLE_SANDBOX'] = '1'
            env['CYPRESS_CRASH_REPORTS'] = '0'
            
            # Run Cypress test
            log.info(f"Running Cypress extraction for Bilibili UID: {uid}")
            result = subprocess.run([
                "npx", "cypress", "run",
                "--spec", "cypress/e2e/bilibili-dynamic.cy.ts",
                "--headless",
                "--browser", "chrome",
                "--config", "chromeWebSecurity=false",
                "--config", "video=false",
                "--config", "screenshotOnRunFailure=false"
            ], 
            cwd=self.project_root,
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout
            )
            
            if result.returncode == 0:
                log.info("Cypress test completed successfully")
            else:
                log.warning(f"Cypress test completed with warnings: {result.stderr}")
            
            # Look for generated fixture files
            return self._extract_data_from_fixtures(uid)
            
        except subprocess.TimeoutExpired:
            log.error(f"Cypress test timed out after {timeout} seconds")
            return None
        except Exception as e:
            log.error(f"Error running Cypress test: {e}")
            return None
    
    def _cleanup_old_fixtures(self, uid: str):
        """Clean up old fixture files for the given UID"""
        try:
            # Remove files older than 1 hour
            cutoff_time = time.time() - 3600  # 1 hour ago
            pattern = f"bilibili-*-{uid}-*.json"
            
            for file_path in self.fixtures_dir.glob(pattern):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    log.debug(f"Cleaned up old fixture file: {file_path}")
        except Exception as e:
            log.warning(f"Error cleaning up old fixtures: {e}")
    
    def _extract_data_from_fixtures(self, uid: str) -> Optional[Dict[str, Any]]:
        """
        Extract data from the generated fixture files
        
        Args:
            uid: Bilibili user ID
            
        Returns:
            Dictionary containing the extracted data or None if not found
        """
        try:
            # Look for success files first
            success_pattern = f"bilibili-dynamic-success-{uid}-*.json"
            success_files = list(self.fixtures_dir.glob(success_pattern))
            
            if success_files:
                # Get the most recent success file
                latest_file = max(success_files, key=lambda p: p.stat().st_mtime)
                log.info(f"Found successful extraction data: {latest_file}")
                
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        'success': True,
                        'data': data.get('response', {}),
                        'url': data.get('url', ''),
                        'headers': data.get('headers', {}),
                        'timestamp': data.get('timestamp', time.time()),
                        'source_file': str(latest_file)
                    }
            
            # Look for retry success files
            retry_success_pattern = f"bilibili-dynamic-retry-success-{uid}-*.json"
            retry_files = list(self.fixtures_dir.glob(retry_success_pattern))
            
            if retry_files:
                latest_file = max(retry_files, key=lambda p: p.stat().st_mtime)
                log.info(f"Found retry success extraction data: {latest_file}")
                
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        'success': True,
                        'data': data.get('response', {}),
                        'url': data.get('url', ''),
                        'headers': data.get('headers', {}),
                        'timestamp': data.get('timestamp', time.time()),
                        'source_file': str(latest_file),
                        'retry_attempt': data.get('attempt', 1)
                    }
            
            # Look for error files to understand what went wrong
            error_pattern = f"bilibili-dynamic-*error*-{uid}-*.json"
            error_files = list(self.fixtures_dir.glob(error_pattern))
            
            if error_files:
                latest_error = max(error_files, key=lambda p: p.stat().st_mtime)
                log.warning(f"Found error extraction data: {latest_error}")
                
                with open(latest_error, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        'success': False,
                        'error': data.get('error', 'Unknown error'),
                        'response': data.get('response', {}),
                        'url': data.get('url', ''),
                        'headers': data.get('headers', {}),
                        'timestamp': data.get('timestamp', time.time()),
                        'source_file': str(latest_error)
                    }
            
            log.error(f"No extraction data found for UID: {uid}")
            return None
            
        except Exception as e:
            log.error(f"Error extracting data from fixtures: {e}")
            return None
    
    def get_cookies_for_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """
        Get cookies extracted for the given UID
        
        Args:
            uid: Bilibili user ID
            
        Returns:
            Dictionary containing cookies or None if not found
        """
        try:
            cookie_pattern = f"bilibili-cookies-{uid}-*.json"
            cookie_files = list(self.fixtures_dir.glob(cookie_pattern))
            
            if cookie_files:
                latest_file = max(cookie_files, key=lambda p: p.stat().st_mtime)
                log.info(f"Found cookies data: {latest_file}")
                
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data
            
            return None
            
        except Exception as e:
            log.error(f"Error extracting cookies: {e}")
            return None
