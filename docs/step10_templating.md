# Step 10: Templating

## Templating Adapters

In this step, we've introduced support for templating engines by creating adapters for both Jinja2 and Mako. 
The adapters allow the `TemplateService` to render templates using the specified engine, based on the configuration.

### Template Adapters

- **JinjaAdapter**: This adapter allows the use of Jinja2 templates. It expects a directory containing the 
  templates and provides methods to render them.
- **MakoAdapter**: This adapter supports Mako templates. Like the Jinja adapter, it renders templates from a 
  specified directory.

*Note that Jinja and Mako use different syntax and features, so you may need to adjust your templates accordingly.*

### TemplateService

- The `TemplateService` dynamically selects the appropriate template engine based on the configuration.
  The engine is chosen from the `TEMPLATE_ENGINE` setting in the configuration, defaulting to Jinja2 if none 
  is specified.

## Lazy Loading

We've also implemented lazy loading for the `TemplateService` within the `RoutingService`. 
This means that the `TemplateService` is only instantiated when it's actually needed, reducing the initial 
overhead and improving performance.

### Benefits of Lazy Loading

- **Efficiency**: Resources are only consumed when necessary, which improves the application's overall efficiency.
- **Scalability**: This approach allows the framework to scale better by initializing services on-demand.

This step has enhanced the framework's flexibility in rendering templates and managing resources more effectively.

Embedding TemplateService within RoutingService does increase coupling, but in the context of a web framework, 
this might be a practical and natural design choice (I guess...)


