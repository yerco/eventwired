# Step 14: Experimental Agnostic ORM Approach

## Overview

In this step, the goal was to create a unified way to manage models across different ORMs, including SQLAlchemy 
and Tortoise, without coupling the framework to a specific ORM. The idea was to allow users to define agnostic
models and use any ORM underneath without significant changes to the model definitions.

This experimental approach aimed to:

- Allow agnostic model definitions using a common interface.
- Enable easy switching between ORMs like SQLAlchemy and Tortoise.
- Abstract CRUD operations for both ORMs in a single service.

However, after experimenting with this approach, a few major concerns arose regarding complexity and design philosophy.
Ultimately, I decided to move towards a more opinionated approach and roll back the changes.

Why I’m Rolling Back This Step

1. Complexity in Supporting Multiple ORMs

    Supporting multiple ORMs introduces too much complexity, both in code and design:

    - Adapters for each ORM were required to translate agnostic model definitions into ORM-specific models.
	- Metadata and table management between ORMs had significant differences that led to issues when dynamically 
      creating models.
	- Error handling and lifecycle management for different ORMs would add substantial overhead.

2. Coupling Between Models and ORMs

    The design introduced a tight coupling between the models and the ORM, which wasn’t desirable:

	- Models should be simple domain classes without being directly tied to the ORM. This coupling 
      limited the flexibility and made the framework more rigid.
	- Instead of focusing on domain logic, the models ended up being too ORM-specific.

3. The Model Service Was Unnecessary

    Having a dedicated Model Service to handle models ended up complicating the design. Models are fundamentally simple
    classes, and trying to abstract them into a service added unnecessary layers:

    - Models can easily be defined as plain Python classes or directly within the ORM without the need
      for additional indirection.
    - The service was over-engineered and did not bring enough value to justify its inclusion.

## Conclusion

The agnostic ORM approach, while initially promising, brought more complexity than benefits. Instead, I will move
forward with a more opinionated approach, focusing on a single ORM (SQLAlchemy) and keeping the models simple and 
straightforward.

This step served as an experiment to explore the feasibility of a unified ORM abstraction, but after evaluating 
the trade-offs, it became clear that sticking to a single, well-supported ORM will make the framework simpler, 
more reliable, and easier to maintain.

Moving forward, I will:

- Rollback the agnostic ORM experiment.
- Focus on SQLAlchemy as the core ORM for this framework.
- Keep models as simple domain classes, decoupled from ORM-specific implementations.
