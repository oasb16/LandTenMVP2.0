# SS2_Pulse — Persona-Based Router

Routes user to the appropriate dashboard view based on persona after login.

## 🔁 Routing Table

| Persona      | Function             | Source Module                               |
|--------------|----------------------|---------------------------------------------|
| tenant       | run_tenant_view()     | superstructures.ss3_echo                    |
| landlord     | run_landlord_view()   | superstructures.ss4_root.landlord_view     |
| contractor   | run_contractor_view() | superstructures.ss4_root.contractor_view   |
| admin        | render_tracker()      | protocol_tracker.landten_protocol_tracker_app |

> Note: `landlord` and `contractor` views are currently placeholders awaiting SS5/SS7 readiness.
