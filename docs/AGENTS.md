# Agent and Skill Reference

This document provides an overview of all custom agents and their associated skills in the Corrupt Video File Inspector project.

## Overview

All agents follow the agent skills specification and best practices. Each agent has:
- A dedicated markdown file in `.github/agents/`
- A corresponding skill file in `.github/skills/<skill-name>/SKILL.md`
- Model specification based on complexity (Haiku for frequent/simple tasks, Sonnet for complex tasks)
- Defined tools and capabilities
- Clear use cases and instructions

## Agent Lifecycle Mapping

Agents are organized by software development lifecycle phase:

### Issue Management Phase
- **Issue Creation Agent** - Issue triage and formatting

### Planning and Design Phase
- **Feature Development Agent** - Feature design and implementation

### Development Phase
- **Feature Development Agent** - Code implementation
- **Refactoring Agent** - Code structure improvements
- **Documentation Agent** - Documentation creation and updates

### Quality Assurance Phase
- **Code Review Agent** - Code quality review
- **Testing Agent** - Test generation and analysis
- **Performance Optimization Agent** - Performance analysis and optimization

## Agents by Model

### Haiku Model (claude-3-5-haiku-20241022)
**Use for**: Frequent, lower-cost operations that require quick responses

1. **Issue Creation Agent**
2. **Code Review Agent**
3. **Testing Agent**
4. **Documentation Agent**

### Sonnet Model (claude-3-5-sonnet-20241022)
**Use for**: Complex, less-frequent operations requiring deep reasoning

1. **Feature Development Agent**
2. **Refactoring Agent**
3. **Performance Optimization Agent**

## Agent Details

### Issue Creation Agent
**Model**: Claude 3.5 Haiku (claude-3-5-haiku-20241022)  
**Location**: `.github/agents/issue-creation-agent.md`  
**Skill**: `.github/skills/issue-creation/SKILL.md`

**Purpose**: Automates issue creation, triage, and formatting

**Capabilities**:
- Analyze unstructured issue content
- Classify issues (bug, feature, documentation, etc.)
- Format issues according to project templates
- Apply appropriate labels
- Preserve original content

**When to Use**:
- Creating new issues for the project
- Triaging unstructured issue submissions
- Reformatting issues to match project templates

---

### Code Review Agent
**Model**: Claude 3.5 Haiku (claude-3-5-haiku-20241022)  
**Location**: `.github/agents/code-review-agent.md`  
**Skill**: `.github/skills/code-review/SKILL.md`

**Purpose**: Automated code review for pull requests

**Capabilities**:
- Check code formatting (Black, 79-char line length)
- Verify type annotations
- Ensure f-string usage
- Validate import organization
- Identify security concerns
- Verify test coverage

**When to Use**:
- Reviewing pull requests before merge
- Validating code changes against project standards
- Checking for Python anti-patterns
- Ensuring test coverage for new features

---

### Testing Agent
**Model**: Claude 3.5 Haiku (claude-3-5-haiku-20241022)  
**Location**: `.github/agents/testing-agent.md`  
**Skill**: `.github/skills/testing/SKILL.md`

**Purpose**: Test generation and analysis

**Capabilities**:
- Generate unit tests for new functions
- Create integration tests
- Generate parametrized tests
- Create test fixtures and mocks
- Analyze test coverage
- Identify untested code paths

**When to Use**:
- Adding new functionality that needs tests
- Analyzing test coverage gaps
- Debugging failing tests
- Improving test quality
- Setting up test fixtures or mocks

---

### Documentation Agent
**Model**: Claude 3.5 Haiku (claude-3-5-haiku-20241022)  
**Location**: `.github/agents/documentation-agent.md`  
**Skill**: `.github/skills/documentation/SKILL.md`

**Purpose**: Documentation creation and maintenance

**Capabilities**:
- Write clear, comprehensive README files
- Generate API documentation
- Create user guides and tutorials
- Update existing documentation
- Ensure consistent formatting
- Validate code examples

**When to Use**:
- Adding new features that need documentation
- Code changes affecting existing documentation
- Improving documentation clarity
- Creating user guides or tutorials
- Documenting APIs or configuration options

---

### Feature Development Agent
**Model**: Claude 3.5 Sonnet (claude-3-5-sonnet-20241022)  
**Location**: `.github/agents/feature-development-agent.md`  
**Skill**: `.github/skills/feature-development/SKILL.md`

**Purpose**: Complex feature implementation

**Capabilities**:
- Analyze requirements and design solutions
- Choose appropriate design patterns
- Write production-quality code
- Implement complex algorithms
- Ensure type safety and error handling
- Write comprehensive tests
- Document new features

**When to Use**:
- Implementing new features from requirements
- Building new modules or components
- Designing complex algorithms or logic
- Integrating external services
- Adding significant new functionality

---

### Refactoring Agent
**Model**: Claude 3.5 Sonnet (claude-3-5-sonnet-20241022)  
**Location**: `.github/agents/refactoring-agent.md`  
**Skill**: `.github/skills/refactoring/SKILL.md`

**Purpose**: Large-scale code refactoring and architecture improvements

**Capabilities**:
- Extract functions and classes
- Reorganize module structure
- Implement design patterns
- Improve separation of concerns
- Modernize legacy code
- Reduce technical debt
- Simplify complex logic

**When to Use**:
- Performing large-scale code reorganization
- Implementing design pattern changes
- Modernizing legacy code
- Improving code architecture
- Reducing technical debt across multiple modules

---

### Performance Optimization Agent
**Model**: Claude 3.5 Sonnet (claude-3-5-sonnet-20241022)  
**Location**: `.github/agents/performance-optimization-agent.md`  
**Skill**: `.github/skills/performance-optimization/SKILL.md`

**Purpose**: Performance analysis and optimization

**Capabilities**:
- Profile code to identify bottlenecks
- Analyze CPU and memory usage
- Optimize algorithms and data structures
- Implement caching strategies
- Add parallelization
- Create performance benchmarks
- Validate optimization effectiveness

**When to Use**:
- Performance issues are reported
- Profiling shows bottlenecks
- Optimizing slow operations
- Reducing resource usage
- Improving scalability

## Using Agents

### Invoking Agents

Agents can be invoked through GitHub Copilot when working on relevant tasks. The system will suggest appropriate agents based on the context of your work.

### Best Practices

1. **Choose the Right Agent**: Select the agent that best matches your current task
2. **Provide Context**: Give the agent sufficient context about the task
3. **Review Agent Output**: Always review and validate agent suggestions
4. **Iterative Refinement**: Work with the agent iteratively to refine solutions
5. **Model Selection**: Trust the model assignments - Haiku for frequent tasks, Sonnet for complex ones

### Model Selection Rationale

**Haiku (claude-3-5-haiku-20241022)**:
- Lower cost per invocation
- Faster response times
- Suitable for well-defined, frequent tasks
- Good for code review, testing, and documentation
- Expected to be invoked many times per day

**Sonnet (claude-3-5-sonnet-20241022)**:
- Higher quality for complex reasoning
- Better for architectural decisions
- Suitable for feature development and refactoring
- Better at understanding complex codebases
- Expected to be invoked less frequently

## Skill Documentation

Each skill provides comprehensive documentation including:

- **When to Use**: Clear guidelines on when to invoke the skill
- **Standards and Requirements**: Project-specific standards and conventions
- **Best Practices**: Proven patterns and approaches
- **Examples**: Concrete code examples and patterns
- **Common Pitfalls**: Mistakes to avoid
- **Tools and Commands**: Relevant commands and tools
- **References**: Links to external resources

## Contributing

When adding new agents or skills:

1. Follow the existing agent/skill template structure
2. Include frontmatter with name, description, model, tools, and skills
3. Assign appropriate model (Haiku vs Sonnet) based on complexity
4. Document capabilities, use cases, and instructions
5. Create comprehensive skill documentation
6. Update this reference document
7. Update `.github/copilot-instructions.md`

## References

- [Agent Skills Specification](https://github.com/github/copilot-instructions)
- [GitHub Copilot Documentation](https://docs.github.com/en/copilot)
- [Custom Agents Best Practices](https://github.com/github/copilot-agents)
