/// <reference types="cypress" />

// Custom command to intercept Bilibili API and extract data
Cypress.Commands.add('getBilibiliDynamic', (uid: string) => {
  // Set up intercept for the Bilibili API
  cy.intercept('GET', '**/x/polymer/web-dynamic/v1/feed/space**', (req) => {
    // Allow the request to continue
    req.continue();
  }).as('bilibiliDynamicAPI');

  // Visit the Bilibili dynamic page
  cy.visit(`/${uid}/dynamic`);
  
  // Wait for the API call to complete
  cy.wait('@bilibiliDynamicAPI', { timeout: 30000 }).then((interception) => {
    // Return the response data
    return cy.wrap(interception.response?.body);
  });
});

// Command to get dynamic data with cookie handling
Cypress.Commands.add('getBilibiliDynamicWithCookies', (uid: string) => {
  let dynamicData: any = null;

  // Set up intercept for the Bilibili API
  cy.intercept('GET', '**/x/polymer/web-dynamic/v1/feed/space**', (req) => {
    // Log request details for debugging
    console.log('Request URL:', req.url);
    console.log('Request Headers:', req.headers);
    req.continue();
  }).as('bilibiliDynamicAPI');

  // Visit the Bilibili dynamic page
  cy.visit(`/${uid}/dynamic`);
  
  // Wait for page to load and API call to complete
  cy.wait('@bilibiliDynamicAPI', { timeout: 30000 }).then((interception) => {
    dynamicData = interception.response?.body;
    console.log('API Response:', dynamicData);
  });

  // Return the captured data
  cy.then(() => {
    return cy.wrap(dynamicData);
  });
});

// Command to save dynamic data to file
Cypress.Commands.add('saveDynamicData', (data: any, uid: string) => {
  const timestamp = Date.now();
  const filename = `bilibili-dynamic-${uid}-${timestamp}.json`;
  
  cy.writeFile(`cypress/fixtures/${filename}`, data);
  
  return cy.wrap(filename);
});

declare global {
  namespace Cypress {
    interface Chainable {
      getBilibiliDynamic(uid: string): Chainable<any>;
      getBilibiliDynamicWithCookies(uid: string): Chainable<any>;
      saveDynamicData(data: any, uid: string): Chainable<string>;
    }
  }
}

export {};
