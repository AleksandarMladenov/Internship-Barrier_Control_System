const API = Cypress.env("API_BASE_URL") || "http://localhost:8001/api";
const api = (path) => `${API}${path}`;

describe("Admin → Role Management", () => {
  const OWNER_EMAIL = "e2e-admin@example.com";
  const VIEWER_EMAIL = "e2e-viewer@example.com";

  const API = Cypress.env("API_BASE_URL") || "http://localhost:8001/api";
  const api = (path) => `${API}${path}`;

  beforeEach(() => {
    cy.loginViaApi(Cypress.env("ADMIN_EMAIL"), Cypress.env("ADMIN_PASSWORD"));

    cy.visit("/admins");

    cy.get('[data-cy="role-management-title"]')
      .should("be.visible")
      .and("contain.text", "Role Management");
  });

  it("renders admins table", () => {
    cy.get('[data-cy="admins-table"]').should("be.visible");
    cy.contains("td", OWNER_EMAIL).should("exist");
    cy.contains("td", VIEWER_EMAIL).should("exist");
  });

  it("owner can change another admin's role (backend verified)", () => {
    // 1) Read current role from backend (true source of truth)
    cy.request("GET", api("/admins")).then((res) => {
      const viewer = res.body.find((a) => a.email === VIEWER_EMAIL);
      expect(viewer, "viewer admin exists").to.exist;

      const current = viewer.role; // "viewer" | "admin" | "owner"
      const next = current === "admin" ? "viewer" : "admin";

      // 2) Change role via UI
      cy.contains("td", VIEWER_EMAIL)
        .parents("tr")
        .within(() => {
          cy.get("select").select(next);
        });

      // 3) Verify backend updated (retry-friendly)
      cy.request({
        method: "GET",
        url: api("/admins"),
        retryOnStatusCodeFailure: true,
        retryOnNetworkFailure: true,
      }).then((res2) => {
        const viewer2 = res2.body.find((a) => a.email === VIEWER_EMAIL);
        expect(viewer2.role).to.eq(next);
      });
    });
  });

  it("owner can deactivate and reactivate an admin", () => {
    cy.intercept("POST", "**/admins/*/deactivate").as("deactivate");
    cy.intercept("POST", "**/admins/*/activate").as("activate");

    cy.contains("td", VIEWER_EMAIL)
      .parents("tr")
      .within(() => {
        cy.contains("button", /deactivate/i).click();
      });

    cy.wait("@deactivate");

    cy.contains("td", VIEWER_EMAIL)
      .parents("tr")
      .contains(/disabled/i);

    cy.contains("td", VIEWER_EMAIL)
      .parents("tr")
      .within(() => {
        cy.contains("button", /activate/i).click();
      });

    cy.wait("@activate");

    cy.contains("td", VIEWER_EMAIL)
      .parents("tr")
      .contains(/active/i);
  });

  it("owner can invite a new admin", () => {
    const invitedEmail = `invite_${Date.now()}@example.com`;

    cy.get('[data-cy="invite-admin-button"]').click();

    cy.get('[data-cy="invite-modal"]').first().within(() => {
      cy.get('input[type="text"]').type("Invited Admin");
      cy.get('input[type="email"]').type(invitedEmail);
      cy.get("select").select("viewer");
      cy.contains("button", /send invite/i).click();

      // close modal (invite sent screen)
      cy.contains(/done|close/i).click();
    });

    cy.contains("td", invitedEmail)
      .parents("tr")
      .contains(/invited/i);
  });

  it("owner can resend invite", () => {
    const invitedEmail = `resend_${Date.now()}@example.com`;

    cy.get('[data-cy="invite-admin-button"]').click();

    cy.get('[data-cy="invite-modal"]').first().within(() => {
      cy.get('input[type="text"]').type("Resend Admin");
      cy.get('input[type="email"]').type(invitedEmail);
      cy.get("select").select("viewer");
      cy.contains("button", /send invite/i).click();
      cy.contains(/done|close/i).click(); // important: remove backdrop
    });

    cy.get('[data-cy="role-filter"]').select("invited");

    cy.contains("td", invitedEmail)
      .parents("tr")
      .within(() => {
        cy.contains("button", /resend/i).click();
      });

    cy.contains(/invite/i).should("exist");
  });

  it("owner cannot change own role", () => {
    cy.contains("td", OWNER_EMAIL)
      .parents("tr")
      .within(() => {
        cy.get("select").should("be.disabled");
      });
  });

  it("viewer cannot see invite button", () => {
    cy.clearCookies();

    cy.loginViaApi("e2e-viewer@example.com", Cypress.env("ADMIN_PASSWORD"));

    cy.visit("/admins");

    cy.get('[data-cy="invite-admin-button"]').should("not.exist");
  });
});
