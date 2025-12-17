describe("Login -> Role Management", () => {
  it("logs in and opens Role Management page", () => {
    const email = Cypress.env("ADMIN_EMAIL");
    const password = Cypress.env("ADMIN_PASSWORD");

    // Fast login through API (sets cookie)
    cy.loginViaApi(email, password);

    // Now open the app
    cy.visit("/admins");

    // Basic “logged in” signal — adjust to what your UI shows
    // Example: Sidebar item, heading, etc.
    cy.contains(/role management|admins|petroff parking/i).should("be.visible");
  });

  it("can reach Role Management screen from UI", () => {
    const email = Cypress.env("ADMIN_EMAIL");
    const password = Cypress.env("ADMIN_PASSWORD");

    cy.visit("/login");

    cy.get('input[type="email"]').type(email);
    cy.get('input[type="password"]').type(password);
    cy.contains("button", /log in/i).click();

    // Your LoginPage redirects to /admins on success
    cy.location("pathname").should("eq", "/admins");

    // If Role Management is a separate route (example "/role-management"),
    // click the sidebar item or navigate directly.
    // Prefer clicking if you have a menu item:
    // cy.contains("a", /role management/i).click();

    // Or direct visit if route is known:
    // cy.visit("/role-management");

    // Assert something unique on RoleManagementPage:
    cy.contains(/invite|role|email/i).should("be.visible");
  });
});
