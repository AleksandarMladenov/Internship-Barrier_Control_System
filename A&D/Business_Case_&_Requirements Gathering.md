# Business Case & Requirements Gathering
**Project: Intelligent Parking Management System**  
**Company: PetroffSoft Ltd.**

---

## **Context**

PetroffSoft Ltd. is a Bulgarian software company specializing in automation, IT infrastructure, and custom software solutions.  
The company has successfully launched products such as:

- **Capella** – cloud-based hotel management system.
- **Friday** – restaurant point-of-sale (POS) system.

Building on these, PetroffSoft is expanding into **smart infrastructure and parking management**.

### **Why now?**
- Growing demand for affordable, automated parking systems.
- Target market: hotels, business centers, and organizations that depend on parking revenue.
- Strategic opportunity for PetroffSoft to diversify and strengthen its reputation as a **regional innovator** in IT solutions.

---

## **Problem Statement**

Current parking management practices are inefficient, costly, and outdated:

- **Manual supervision** → requires staff, prone to errors, and slows operations.
- **SIM card–controlled barriers** → lack integration with payments and monitoring.
- **Standalone ticket stations** → too expensive for smaller operators.

### **Impact of the problem:**
- **Revenue leakage** due to lack of reliable fee collection.
- **High operational costs** for parking operators.
- **Poor customer experience** for end users.

PetroffSoft identified this gap as both a **market need** and a **strategic opportunity**.

---

## **Proposed Solution: Intelligent Parking Management System**

A **server-based full-stack application** that integrates license plate recognition (LPR), automated barrier control, and payment processing in a single workflow.

### **Key Features**

**A) License Plate Recognition (LPR):**
- Integration with RTSP camera input (OpenCV + EasyOCR/OpenALPR).
- Recognition of whitelisted (authorized), blacklisted (unauthorized), and subscription vehicles.

**B) Automated Barrier Control:**
- Barrier operated via Raspberry Pi GPIO or Arduino relay.
- Manual override option with mandatory reason logging for accountability.

**C) Payment Processing:**
- Hourly billing and prepaid subscription options.
- Integration with Stripe/PayPal in test mode, plus support for cash.

**D) Operator Web Dashboard (React/Vue):**
- Role-based access control (Operator vs. Admin).
- Key screens: Dashboard, Sessions, Pricing, White/Black Lists, Payments.
- Real-time occupancy and event monitoring.

**E) Reporting & Future Scalability:**
- Reporting templates for revenue and occupancy trends.
- Foundation for cloud-based analytics (dynamic pricing, forecasting, advanced reporting).

---

## **Requirements Gathering**

### **Functional Requirements**
- License plate recognition from RTSP camera streams.
- Whitelist/blacklist CRUD management.
- Session lifecycle (entry → pricing → payment → exit).
- Automated barrier control with manual override.
- Web dashboard (operator/admin workflows).
- Basic reporting templates.

### **Non-Functional Requirements**
- **Scalability:** architecture prepared for multi-site and cloud analytics.
- **Security:** HTTPS/TLS, secure communication with devices, authentication.
- **Reliability:** low-latency barrier response, high LPR accuracy in various conditions.
- **Maintainability:** modular, well-documented, API-driven design.

### **Research Requirements**
- Evaluate OCR libraries (EasyOCR, OpenALPR, Tesseract, YOLO-based).
- Compare architectures: edge vs. server vs. hybrid.
- Explore secure communication protocols (TLS, MQTT, WebSocket).
- Investigate payment provider flows (Stripe, PayPal, subscription handling).
- Research groundwork for predictive analytics and dynamic pricing.

---

## **Conclusion**

This project delivers a **minimum viable product (MVP)** that solves real problems for parking operators while positioning PetroffSoft for future growth in the smart infrastructure domain.  
The system directly addresses **efficiency, revenue protection, and customer experience** while laying the foundation for advanced analytics and scalability.  
