# Cypress Integration for Bilibili Dynamic Fetching

This integration provides a more stable way to fetch Bilibili dynamic data by using Cypress to load the actual webpage and intercept the API calls, avoiding issues with cookie/buvid3 management.

## Prerequisites

1. **Node.js and npm**: Install Node.js (version 16 or higher)
   ```bash
   # On Ubuntu/Debian
   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
   sudo apt-get install -y nodejs
   
   # Or using snap
   sudo snap install node --classic
   
   # Verify installation
   node --version
   npm --version
   ```

2. **Chrome/Chromium**: Cypress requires Chrome or Chromium browser
   ```bash
   # Install Chrome
   wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
   echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
   sudo apt update
   sudo apt install google-chrome-stable
   
   # Or install Chromium
   sudo apt install chromium-browser
   ```

## Installation

1. **Install Node.js dependencies**:
   ```bash
   cd /home/xcao/my-repos/aio-dynamic-push
   npm install
   ```

2. **Verify Cypress installation**:
   ```bash
   npx cypress verify
   ```

## Configuration

To enable Cypress-based fetching in your Bilibili query configuration, add the `use_cypress` option:

```yaml
# config.yml example
query_task:
  - name: "bilibili_cypress"
    enable: true
    type: "bilibili"
    use_cypress: true  # Enable Cypress-based fetching
    uid_list:
      - "322005137"
    enable_dynamic_check: true
    enable_living_check: false
    begin_time: "00:00"
    end_time: "23:59"
    skip_forward: true
```

## Usage

### Manual Testing

1. **Test Cypress extraction directly**:
   ```bash
   python test_cypress_integration.py
   ```

2. **Run Cypress test manually**:
   ```bash
   npx cypress run --spec "cypress/e2e/bilibili-dynamic.cy.ts"
   ```

3. **Open Cypress GUI for debugging**:
   ```bash
   npx cypress open
   ```

### Integration with Main Application

The integration is automatic when `use_cypress: true` is set in the configuration. The system will:

1. Use `CypressRunner` to launch a headless browser
2. Navigate to the Bilibili dynamic page
3. Intercept the API calls to capture the response
4. Extract and process the dynamic data
5. Save the results for debugging in `cypress/fixtures/`

## How It Works

### 1. Browser Automation
- Cypress launches a real Chrome browser (headless)
- Navigates to `https://space.bilibili.com/{uid}/dynamic`
- Waits for the page to load and API calls to complete

### 2. API Interception
- Intercepts calls to `/x/polymer/web-dynamic/v1/feed/space`
- Captures both request headers and response data
- Handles cookies automatically through the browser

### 3. Data Processing
- Extracts the JSON response from the API call
- Processes the dynamic items using the same logic as the original method
- Maintains compatibility with existing push notification logic

### 4. Error Handling
- Retry mechanism for failed requests
- Saves both successful and failed responses for debugging
- Falls back to original method if Cypress fails

## Files Structure

```
aio-dynamic-push/
├── cypress/
│   ├── e2e/
│   │   └── bilibili-dynamic.cy.ts     # Main test file
│   ├── fixtures/                      # Captured data storage
│   └── support/
│       ├── commands.ts                # Custom Cypress commands
│       └── e2e.ts                     # Support file
├── common/
│   └── cypress_runner.py              # Python wrapper for Cypress
├── query_task/
│   └── query_bilibili.py              # Modified with Cypress support
├── cypress.config.ts                  # Cypress configuration
├── package.json                       # Node.js dependencies
└── test_cypress_integration.py        # Integration test script
```

## Debugging

### 1. Check Cypress Logs
Cypress logs are saved in the terminal output when running tests.

### 2. Inspect Captured Data
Check the `cypress/fixtures/` directory for captured API responses:
- `bilibili-dynamic-success-{uid}-{timestamp}.json` - Successful captures
- `bilibili-dynamic-error-{uid}-{timestamp}.json` - Failed captures
- `bilibili-cookies-{uid}-{timestamp}.json` - Extracted cookies

### 3. Run in GUI Mode
For visual debugging:
```bash
npx cypress open
```

## Troubleshooting

### Common Issues

1. **Chrome not found**:
   - Install Chrome or Chromium browser
   - Set `CYPRESS_BROWSER_PATH` environment variable if needed

2. **Permission denied**:
   - Ensure proper permissions for Chrome executable
   - Run with `--no-sandbox` flag in headless environments

3. **Network timeouts**:
   - Increase timeout values in `cypress.config.ts`
   - Check network connectivity to bilibili.com

4. **API rate limiting**:
   - Add delays between requests
   - Use different user agents or request headers

### Environment Variables

Set these environment variables for customization:

```bash
export CYPRESS_BILIBILI_UID="322005137"          # Default UID for testing
export CYPRESS_BROWSER_PATH="/usr/bin/google-chrome"  # Chrome path
export CYPRESS_VIDEO=false                       # Disable video recording
```

## Advantages over Traditional Method

1. **No Cookie Management**: Browser handles cookies automatically
2. **No buvid3 Issues**: Real browser session eliminates authentication problems  
3. **Better Anti-Detection**: Mimics real user behavior
4. **Debugging Friendly**: Can see exactly what the browser sees
5. **Robust**: Handles dynamic page loading and JavaScript execution

## Performance Considerations

- Cypress adds overhead (~10-30 seconds per request)
- Uses more system resources (browser + automation)
- Consider using traditional method for frequent polling
- Use Cypress method for critical/problematic accounts

## Security Notes

- Runs in headless mode by default (no GUI)
- Can capture and store cookies (review fixture files)
- Network requests are logged (may contain sensitive data)
- Consider running in isolated environment for production use
