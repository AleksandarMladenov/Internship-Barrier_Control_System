//describe("Accept Invite → Auto Login", () => {
//  const API = Cypress.env("API_BASE_URL") || "http://localhost:8001/api";
//
//  const apiUrl = (path) => `${API}${path}`;
//
//  const OWNER_EMAIL = Cypress.env("ADMIN_EMAIL") || "e2e-admin@example.com";
//  const OWNER_PASSWORD = Cypress.env("ADMIN_PASSWORD") || "Passw0rd123!";
//
//  it("invites a new admin and accepts the invite, then lands in /admins", () => {
//    const invitedEmail = `invite_accept_${Date.now()}@example.com`;
//    const invitedName = "Invited Admin";
//    const invitedPassword = "Passw0rd123!";
//
//    // 1) Login as owner via API to get auth cookie for invite endpoint
//    cy.request({
//      method: "POST",
//      url: apiUrl("/auth/login"),
//      body: { email: OWNER_EMAIL, password: OWNER_PASSWORD },
//    }).then((loginRes) => {
//      expect(loginRes.status).to.eq(200);
//
//      // 2) Invite user (backend returns invite_url)
//      return cy.request({
//        method: "POST",
//        url: apiUrl("/admins/invite"),
//        body: {
//          email: invitedEmail,
//          name: invitedName,
//          role: "viewer",
//        },
//      });
//    }).then((inviteRes) => {
//      expect(inviteRes.status).to.eq(201);
//      expect(inviteRes.body).to.have.property("invite_url");
//
//      const inviteUrl = inviteRes.body.invite_url;
//      const invitePath =
//        (() => {
//          try {
//            const u = new URL(inviteUrl);
//            return `${u.pathname}${u.search}`;
//          } catch {
//            // if backend returns a relative URL for some reason
//            return inviteUrl;
//          }
//        })();
//
//      // 3) Open accept-invite page
//      cy.visit(invitePath);
//
//      // 4) Fill accept form (selectors are resilient)
//      cy.get('input[name="name"], input[placeholder*="name" i], input[type="text"]')
//        .first()
//        .clear()
//        .type(invitedName);
//
//      cy.get('input[name="password"], input[placeholder*="password" i], input[type="password"]')
//        .first()
//        .clear()
//        .type(invitedPassword);
//
//      // Some UIs have confirm password — if it exists, fill it too
//      cy.get("body").then(($body) => {
//        const confirmSel =
//          'input[name="confirm_password"], input[name="confirmPassword"], input[placeholder*="confirm" i]';
//        if ($body.find(confirmSel).length) {
//          cy.get(confirmSel).first().clear().type(invitedPassword);
//        }
//      });
//
//      // Submit (button text differs across UIs, so we match broadly)
//      cy.contains(
//        "button",
//        /accept|set password|join|continue|submit|activate/i
//      ).click();
//
//      // 5) Expect auto-login redirect to /admins
//      cy.location("pathname", { timeout: 15000 }).should("eq", "/admins");
//
//      // 6) Confirm the dashboard loaded
//      cy.get('[data-cy="role-management-title"]', { timeout: 15000 })
//        .should("be.visible")
//        .and("contain.text", "Role Management");
//
//      // 7) Extra: confirm backend session is actually the invited user
//      cy.request({
//        method: "GET",
//        url: apiUrl("/auth/me"),
//      }).then((meRes) => {
//        expect(meRes.status).to.eq(200);
//        expect(meRes.body.email).to.eq(invitedEmail);
//      });
//    });
//  });
//});
