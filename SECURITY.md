# Security Policy

## Branch Protection and Code Review Requirements

### Main Branch Protection

The `main` branch is protected with the following requirements:

- **Code Owner Review Required**: All pull requests to `main` require approval from designated code owners
- **Status Checks**: CI/CD pipeline must pass before merging
- **Dismiss Stale Reviews**: Reviews are automatically dismissed when new commits are pushed
- **No Force Push**: Force pushes to `main` are not allowed

### Code Ownership

This repository uses GitHub CODEOWNERS to ensure critical files receive appropriate review:

- **Repository Owner**: @tdorsey is the primary code owner for all files
- **Critical Configuration**: `.github/settings.yml` requires admin approval
- **Security Files**: `SECURITY.md` and related security documentation require admin approval  
- **Workflow Files**: All `.github/workflows/` files require admin approval
- **CODEOWNERS**: The CODEOWNERS file itself requires admin approval

### Permission Model

#### Configuration File Protection

The `.github/settings.yml` file controls repository settings and security policies. Changes to this file:

1. **Must be reviewed by code owners** (enforced automatically)
2. **Require admin approval** for sensitive configuration changes
3. **Cannot be bypassed** even by repository admins (when enforce_admins is enabled)

#### Impact on Development Workflow

⚠️ **Important**: Enabling "require code owner review" on the main branch means:

- **All pull requests** to `main` require code owner approval, not just changes to `.github/settings.yml`
- **Development workflow** may be slower due to required admin reviews
- **Code owners** (@tdorsey) must be available to review and approve changes

### Security Best Practices

1. **Principle of Least Privilege**: Only necessary permissions are granted
2. **Defense in Depth**: Multiple layers of protection for critical files
3. **Audit Trail**: All changes to protected files are logged and reviewable
4. **Documentation**: Security policies are documented and version-controlled

### Repository Settings Configuration

If you're using a GitHub App like Probot Settings, the `.github/settings.yml` file will automatically configure:

- Branch protection rules
- Repository settings
- Security policies
- Labels and automation

### Manual Configuration Required

Some security settings must be configured manually in the GitHub repository settings:

1. **Navigate to**: Repository Settings → Branches
2. **Configure main branch protection**:
   - ✅ Require pull request reviews before merging
   - ✅ Require review from code owners
   - ✅ Dismiss stale reviews when new commits are pushed
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Include administrators (optional, based on security requirements)

## Reporting Security Issues

If you discover a security vulnerability, please:

1. **Do NOT** open a public issue
2. **Contact** the repository owner directly: @tdorsey
3. **Provide** detailed information about the vulnerability
4. **Allow** reasonable time for assessment and remediation

## Security Updates

This document will be updated as security policies evolve. All changes to security policies require code owner review as enforced by the CODEOWNERS file.
