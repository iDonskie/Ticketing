# Requirements Traceability Matrix (RTM) & Test Cases

## 1. Requirements Traceability Matrix (RTM)

| Req ID | Requirement Description | Test Case ID | Status |
| :--- | :--- | :--- | :--- |
| REQ-01 | Account Creation System (Admin, Requestor, Developer) | TC-01 | PASS |
| REQ-02 | Login & Password Reset System | TC-02, TC-03 | PASS |
| REQ-03 | Create a Ticket Function | TC-04 | PASS |
| REQ-04 | Assign a Ticket Function | TC-05 | PASS |
| REQ-05 | Mark Ticket as Resolved | TC-06 | PASS |
| REQ-06 | Notify User System | TC-07 | PASS |

---

## 2. Test Cases

### TC-01: User Registration
- **Steps:** Submit registration form with unique username, password, and role.
- **Expected Result:** Database creates user record; alert confirms account creation.

### TC-02: User Login
- **Steps:** Enter valid username and password on the login screen.
- **Expected Result:** Dashboard loads displaying user ID, username, role, and authorized sidebar options.

### TC-03: Reset Password
- **Steps:** Enter existing username and new password in the Reset Password form.
- **Expected Result:** Database record updates; user can log in with new password.

### TC-04: Create Ticket
- **Steps:** Log in as Requestor, navigate to "Create Ticket", enter title/description, and submit.
- **Expected Result:** Ticket created with default status `Open`.

### TC-05: Assign Ticket
- **Steps:** Log in as Admin, navigate to "Assign Ticket", enter Ticket ID and Developer User ID.
- **Expected Result:** Ticket record `assigned_to` updates to Developer ID.

### TC-06: Resolve Ticket
- **Steps:** Log in as Developer, navigate to "Resolve Ticket", enter Ticket ID, and click Resolve.
- **Expected Result:** Ticket status updates to `Resolved`.

### TC-07: Verify Notifications
- **Steps:** Review ticket details in "All Tickets" view after assignment or resolution.
- **Expected Result:** Notification banner displays within the ticket card detailing assignment/resolution events.