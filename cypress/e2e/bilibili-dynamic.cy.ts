/// <reference types="cypress" />

describe('Bilibili Dynamic Data Extraction', () => {
  const uid = Cypress.env('BILIBILI_UID') || '322005137';
  
  beforeEach(() => {
    // Set up common headers and user agent to mimic real browser
    cy.intercept('**', (req) => {
      req.headers['user-agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';
      req.headers['accept-language'] = 'zh-CN,zh;q=0.9,en;q=0.8';
    });
  });

  it('should extract Bilibili dynamic data via API interception', () => {
    let capturedData: any = null;
    let apiUrl: string = '';
    let requestHeaders: any = {};

    // Set up intercept for the Bilibili dynamic API
    cy.intercept('GET', '**/x/polymer/web-dynamic/v1/feed/space**', (req) => {
      console.log('Intercepted API request:', req.url);
      apiUrl = req.url;
      requestHeaders = req.headers;
      
      // Continue with the request
      req.continue((res) => {
        console.log('API Response status:', res.statusCode);
        console.log('API Response body:', res.body);
        capturedData = res.body;
      });
    }).as('bilibiliDynamicAPI');

    // Visit the Bilibili dynamic page
    cy.visit(`/${uid}/dynamic`, {
      timeout: 30000,
      failOnStatusCode: false
    });

    // Wait for the page to load and API call to complete
    cy.wait('@bilibiliDynamicAPI', { timeout: 30000 }).then((interception) => {
      expect(interception.response).to.exist;
      
      const responseBody = interception.response?.body;
      console.log('Final captured data:', responseBody);

      // Validate the response structure
      if (responseBody && responseBody.code === 0) {
        expect(responseBody).to.have.property('data');
        expect(responseBody.data).to.have.property('items');
        
        // Save the successful response
        const timestamp = Date.now();
        const filename = `bilibili-dynamic-success-${uid}-${timestamp}.json`;
        cy.writeFile(`cypress/fixtures/${filename}`, {
          url: interception.request.url,
          headers: interception.request.headers,
          response: responseBody,
          timestamp: timestamp
        });
        
        console.log(`Data saved to: ${filename}`);
      } else {
        // Save the error response for debugging
        const timestamp = Date.now();
        const filename = `bilibili-dynamic-error-${uid}-${timestamp}.json`;
        cy.writeFile(`cypress/fixtures/${filename}`, {
          url: interception.request.url,
          headers: interception.request.headers,
          response: responseBody,
          timestamp: timestamp,
          error: 'API returned non-zero code or empty response'
        });
        
        console.log(`Error data saved to: ${filename}`);
        console.log('Response code:', responseBody?.code);
        console.log('Response message:', responseBody?.message);
      }
    });

    // Also try to get cookies for future use
    cy.getCookies().then((cookies) => {
      console.log('Current cookies:', cookies);
      
      const timestamp = Date.now();
      const cookieFilename = `bilibili-cookies-${uid}-${timestamp}.json`;
      cy.writeFile(`cypress/fixtures/${cookieFilename}`, {
        cookies: cookies,
        timestamp: timestamp,
        uid: uid
      });
    });
  });

  it('should extract dynamic data with retry mechanism', () => {
    let attempts = 0;
    const maxAttempts = 3;

    function attemptExtraction() {
      attempts++;
      console.log(`Attempt ${attempts} of ${maxAttempts}`);

      cy.intercept('GET', '**/x/polymer/web-dynamic/v1/feed/space**', (req) => {
        // Add headers that might help avoid detection
        req.headers['referer'] = `https://space.bilibili.com/${uid}/dynamic`;
        req.headers['origin'] = 'https://space.bilibili.com';
        req.headers['sec-fetch-dest'] = 'empty';
        req.headers['sec-fetch-mode'] = 'cors';
        req.headers['sec-fetch-site'] = 'same-site';
        
        req.continue();
      }).as(`bilibiliDynamicAPI_${attempts}`);

      cy.visit(`/${uid}/dynamic`, { timeout: 30000 });

      cy.wait(`@bilibiliDynamicAPI_${attempts}`, { timeout: 30000 }).then((interception) => {
        const responseBody = interception.response?.body;
        
        if (responseBody && responseBody.code === 0 && responseBody.data && responseBody.data.items) {
          // Success - save the data
          const timestamp = Date.now();
          const filename = `bilibili-dynamic-retry-success-${uid}-${timestamp}.json`;
          cy.writeFile(`cypress/fixtures/${filename}`, {
            attempt: attempts,
            url: interception.request.url,
            headers: interception.request.headers,
            response: responseBody,
            timestamp: timestamp
          });
          console.log(`Success on attempt ${attempts}, data saved to: ${filename}`);
        } else if (attempts < maxAttempts) {
          // Retry if not at max attempts
          console.log(`Attempt ${attempts} failed, retrying...`);
          cy.wait(2000); // Wait 2 seconds before retry
          attemptExtraction();
        } else {
          // Max attempts reached, save error data
          const timestamp = Date.now();
          const filename = `bilibili-dynamic-retry-failed-${uid}-${timestamp}.json`;
          cy.writeFile(`cypress/fixtures/${filename}`, {
            totalAttempts: attempts,
            url: interception.request.url,
            headers: interception.request.headers,
            response: responseBody,
            timestamp: timestamp,
            error: 'Max retry attempts reached'
          });
          console.log(`All ${maxAttempts} attempts failed, error data saved to: ${filename}`);
        }
      });
    }

    attemptExtraction();
  });
});
