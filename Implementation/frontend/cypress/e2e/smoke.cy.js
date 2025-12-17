describe("Smoke", () => {
  it("loads login page", () => {
    cy.visit("/login");
    cy.contains(/login/i);
  });
});
