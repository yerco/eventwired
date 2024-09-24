# Step 15: Housekeeping and Reflections

## Overview

During this phase, we encountered several challenges around how we structured our models, ORM services, and 
the coupling of these with the framework. After an initial attempt at a more complex design, which included a
models service and tight ORM coupling, we rolled back to a simplified approach. 
This document outlines the lessons learned, especially from a Domain-Driven Design (DDD) perspective, 
and highlights improvements we made.

## Initial Approach and Issues

The first attempt involved creating an ORM-agnostic models service. The intent was to have an abstract layer that 
could switch between different ORMs (e.g., SQLAlchemy and Tortoise). This resulted in:
- Tight coupling between models and the ORM, forcing models to inherit from an ORM-specific base class.
- The introduction of an unnecessary models service, where the models were tied too closely to ORM logic.
- Complexity in initialization, which made switching between ORMs difficult and increased the cognitive load for users.

### Problems Identified
1. **Violation of DDD principles**: In DDD, models (especially entities and value objects) should represent 
   the business domain without being polluted by infrastructure concerns like ORM logic. By coupling models 
   with the ORM, we mixed infrastructure code (ORM) into the core domain layer (entities).

2. **Service Overhead**: The creation of a models service added unnecessary complexity. The models service was 
   mainly used to register models and pass them to the ORM. This added layers of indirection without providing 
   clear benefits.

3. **Tight Coupling**: The initial approach tightly coupled models to the ORM service. This limited flexibility
   and introduced hidden dependencies, making it difficult to change or extend functionality.

## Lessons Learned

### 1. Separation of Concerns
One of the key takeaways is the importance of keeping the domain logic clean and separate from infrastructure concerns.
The models should represent the business domain and should not be aware of how they are stored or retrieved.
This aligns with DDD principles, where entities and value objects are pure domain concepts, and repositories 
or services handle persistence.

### 2. Simplicity Over Abstraction
While abstraction is powerful, over-abstracting too early can lead to unnecessary complexity. The attempt to create
a models service that was ORM-agnostic added complexity without significant benefits. By rolling back to a simpler
approach where models are defined independently and tied to a single ORM (SQLAlchemy), we made the system more
understandable and easier to maintain.

### 3. Domain-Driven Design Alignment
In DDD, services should handle business logic that spans across multiple entities or value objects. In the initial
design, we misunderstood the role of services and mixed infrastructure concerns (ORM logic) into the service layer.
Moving forward, the ORM logic should live within repositories or infrastructure layers, keeping services clean
and focused on business rules.

### 4. Repositories vs. Services
Instead of creating a models service, a better approach would be to use repositories that abstract the database
operations for each aggregate or entity. This way, the business logic in services doesn’t depend directly on the ORM,
maintaining a clean separation.

## Final Design

### Simpler Approach
In the final design:
- **No more models service**: We removed the models service entirely. Models are now just classes that inherit from 
  a shared SQLAlchemy base. This avoids unnecessary layers of abstraction.
- **Centralized Base for Models**: We introduced a centralized `Base` class for models, allowing them to share the 
  same metadata and be managed more easily by SQLAlchemy.
- **ORM Service as a Repository**: The `ORMService` now acts as a repository of sorts, handling interactions
  with the database, but without coupling the models to any specific ORM logic.

### Practicality
The revised design is easier for users to understand. Users no longer have to register models in a service
or deal with the complexities of switching ORMs. Models are defined using the SQLAlchemy base, and the ORM
service takes care of the database logic.

## Conclusion

This exercise highlighted the importance of starting simple and adding complexity only when necessary.
We initially tried to over-abstract and accommodate multiple ORMs, which backfired in terms of complexity 
and misalignment with DDD principles. By rolling back and simplifying the design, we not only reduced the 
cognitive load on users but also created a cleaner separation between domain logic and infrastructure.
