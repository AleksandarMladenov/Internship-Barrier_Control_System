describe("Visitor Receipt (seeded session, no Stripe)", () => {
  it("renders a paid receipt for a visitor session", () => {
    const sid = Cypress.env("VISITOR_SESSION_ID");
    expect(sid, "VISITOR_SESSION_ID must be set").to.exist;

    // Intercept session fetch
    cy.intercept("GET", new RegExp(`/sessions/${sid}`)).as("getSession");

    cy.visit(`/receipt?session_id=${sid}`);

    // Wait until backend responds
    cy.wait("@getSession");

    // Receipt page shell
    cy.contains("Receipt", { timeout: 10000 }).should("be.visible");

    // Session footer (very stable)
    cy.contains(`Session #${sid}`, { timeout: 10000 }).should("be.visible");

    // Paid badge or label (status-based)
    cy.contains(/paid/i, { timeout: 10000 }).should("be.visible");

    // Time rows (entry / exit)
    cy.contains(/entry/i).should("be.visible");
    cy.contains(/exit/i).should("be.visible");

    // Amount row
    cy.contains(/paid/i).should("be.visible");

    // Optional email input (only if EMAIL_EP is set)
    cy.get("input[type=email]").should("exist");
  });
});
