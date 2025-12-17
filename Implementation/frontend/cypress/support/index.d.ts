declare namespace Cypress {
  interface Chainable {
    loginViaApi(email: string, password: string): Chainable<void>;
  }
}
