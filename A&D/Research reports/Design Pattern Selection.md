Design Pattern Selection 
1. Introduction

In the implementation of mine Internship assignment, software architecture plays a critical role in ensuring that the system remains scalable, maintainable, and easy to extend. Since the project integrates multiple external components—such as OCR (for license plate recognition), payment gateways, and physical hardware interfaces like Raspberry Pi or Arduino relay modules—choosing an appropriate design pattern is crucial to manage the growing complexity while maintaining clean separation of concerns.

The aim of this section is to explore possible design patterns, evaluate their suitability using decision-based criteria, and provide a rationale for the final selection. The chosen pattern must align with the project’s goals:

Lightweight and easy to comprehend for a Minimum Viable Product (MVP);

Extensible for future hardware and API integrations;

Compatible with FastAPI and layered backend structure (API → Service → Repository);

Simple enough for future contributors to adopt without steep learning curves.

2. Candidate Design Patterns

Several classical design patterns were considered, each offering distinct advantages in terms of modularity, extensibility, and control of object creation or behavior.

2.1 Factory Pattern

The Factory pattern provides a way to create objects without specifying their exact concrete class. It allows the system to decide which implementation of an interface to instantiate at runtime based on configuration or context.

In this project, it can be used to instantiate different OCR engines, payment providers, or barrier control modules depending on the deployment environment (development, testing, or production).

2.2 Strategy Pattern

The Strategy pattern defines a family of algorithms, encapsulates each one, and makes them interchangeable. It promotes flexibility in algorithm selection, such as dynamically switching between EasyOCR and OpenALPR for license plate recognition under varying environmental conditions.

2.3 Adapter Pattern

The Adapter pattern allows classes with incompatible interfaces to work together. It is useful when integrating third-party APIs, SDKs, or hardware libraries that need to conform to the project’s defined interfaces.

2.4 Singleton Pattern

The Singleton pattern ensures that only one instance of a class exists throughout the application lifecycle. This can be useful for shared resources such as configuration management, database sessions, or hardware access.

2.5 State Pattern

The State pattern allows an object to change its behavior when its internal state changes. This can be applied to the Parking Session entity to model transitions between states such as ENTERED, PENDING_PAYMENT, PAID, and EXITED.

3. Decision-Based Criteria Evaluation

| **Criterion**                         | **Factory**                                                    | **Strategy**                      | **Adapter**                  | **Singleton**          | **State**                    |
| ------------------------------------- |----------------------------------------------------------------| --------------------------------- | ---------------------------- | ---------------------- | ---------------------------- |
| **Ease of Implementation**            | Simple, minimal boilerplate                                    |  Moderate (requires multiple strategies) |  Moderate (extra wrapper classes) |  Very simple           | ️ Moderate (state machine logic) |
| **Comprehensibility**                 | Easy for beginners to grasp                                    |  Slightly more abstract           | ️ Requires interface mapping |  Straightforward       | ️ Moderate conceptual overhead |
| **Alignment with System Structure**   |  Perfectly fits layered backend (FastAPI + Services + Repositories) |  Good for runtime algorithm choice |  Useful for 3rd party integrations |  Limited to global configs |  Useful for session transitions |
| **Extensibility / Scalability**       |  High — easily add new OCR or payment types                    |  High — new strategies are independent |  High — add new adapters for APIs | ️ Limited              |  Moderate — new states can be added |
| **Runtime Flexibility**               |  Config-driven provider selection                              |  Runtime algorithm swap           | ️ Static, wrapper-level      | ️ Static, global       |  Limited to entity state     |
| **Reusability**                       |  High                                                          |  High                             |  High                        | ️ Low                  |  Low                         |
| **Suitability for MVP & IoT Context** |  Excellent — low complexity, high practicality                 | ️ Medium — slightly more overhead | ️ Medium                     | ️ Medium — risk of misuse | ️ Medium                     |
| **Testing / Mocking Ease**            |  Excellent — mock factories easily                             |  Excellent                        |  Excellent                   | ️ Medium               |  Requires setup of transitions |


4. Decision and Justification

After analyzing the design alternatives, the Simple Factory Pattern emerged as the most suitable choice for the current phase of the project.

Rationale

Simplicity and Clarity

The Factory pattern offers a clean, minimal way to instantiate different infrastructure components (e.g., OCR modules, payment gateways, barrier controllers) using a unified configuration-based interface.

It is easily explainable and readable for new contributors.

Alignment with System Structure

The existing project follows a clean layered architecture:
API → Service → Repository → Model
The Factory seamlessly fits between the core (business logic) and adapters (infrastructure) layers.

Extensibility

New providers (e.g., another payment gateway or OCR engine) can be integrated by simply registering them in the factory without altering core logic.

Configurability

The factory allows runtime configuration via environment variables (.env file), enabling easy switching between production and mock implementations.

Lightweight Singleton Behavior

By caching created objects using Python’s lru_cache, the Factory also serves as a safe singleton, ensuring heavy objects (like OCR models) are loaded only once.

Ease of Testing

Mocks can be easily registered in the Factory for local testing or CI environments, decoupling hardware and payment dependencies.

5. Example Integration Overview

Factory in Action:

When the system boots, the Factory reads environment variables:

OCR_IMPL=easyocr
PAYMENT_IMPL=stripe
BARRIER_IMPL=rpi


The Factory then instantiates the matching adapter:

EasyOCROCR for license plate recognition

StripePayment for payment processing

RPiBarrier for hardware control

For local testing, these can be changed to:

OCR_IMPL=mock
PAYMENT_IMPL=mock
BARRIER_IMPL=mock


instantly switching to simulated adapters—no code changes required.

This modular approach encapsulates implementation details while keeping the overall structure easy to understand and extend.

6. Conclusion

The Simple Factory Pattern provides the ideal balance between simplicity, scalability, and clarity for the Intelligent Parking Management System.

It supports the plug-and-play nature of various components (OCR, payment, IoT hardware), fits naturally within the FastAPI-based layered architecture, and requires minimal learning curve or refactoring.

While patterns like Strategy, Adapter, or State can complement the system in future iterations (e.g., for OCR optimization or session lifecycle), the Factory Pattern serves as the foundational design decision for ensuring flexibility and maintainability in the current MVP stage.

7. Summary Table

| **Selected Pattern**       | **Implementation Effort** | **Complexity** | **Extensibility** | **Testability** | **Justification Summary**                                                                                                                    |
| -------------------------- | ------------------------- | -------------- | ----------------- | --------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **Simple Factory Pattern** | Low                       | Low            | High              | High            | Provides configurable instantiation for multiple adapters; aligns perfectly with system’s modular architecture; easy to maintain and extend. |
