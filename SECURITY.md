# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in file2MD, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please email **[INSERT SECURITY EMAIL]** with:

1. A description of the vulnerability.
2. Steps to reproduce the issue.
3. Potential impact.
4. Suggested fix (if any).

We will acknowledge receipt within 48 hours and provide a detailed response within 7 days.

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest `main` | ✅ |

## Security Considerations

file2MD processes user-uploaded files. The following security measures are implemented:

### File Upload Security

- **Size limits**: Configurable maximum upload size (default 50 MB).
- **Type validation**: Extension whitelist, MIME type checking, and file signature verification.
- **Safe filenames**: Uploaded files are saved with generated UUID names; original filenames are sanitised before use in responses.
- **Isolated processing**: Files are processed in isolated temporary directories.
- **Automatic cleanup**: Temporary files are deleted after conversion completes or fails.

### Processing Security

- **No script execution**: Uploaded files and their embedded scripts are never executed.
- **No shell injection**: No shell commands are constructed from user-controlled values.
- **Conversion timeouts**: Configurable timeout prevents resource exhaustion from malicious documents.
- **Content validation**: Empty or failed conversions are reported as errors, never as successes.

### Network Security

- **CORS**: Configured to allow only the expected frontend origin.
- **No secrets in images**: All configuration is via environment variables.
- **No authentication data stored**: file2MD does not store user data or require authentication.

### Data Privacy

- **No persistent storage**: Uploaded files are not retained after conversion.
- **No logging of file contents**: Structured logging excludes document content.
- **No telemetry**: file2MD does not send data to external services.

## Dependency Security

Dependencies are pinned and regularly reviewed. Security advisories for dependencies are monitored through:

- GitHub Dependabot alerts
- CI dependency scanning

## Disclosure Policy

We follow [coordinated vulnerability disclosure](https://en.wikipedia.org/wiki/Coordinated_vulnerability_disclosure). We will credit reporters in release notes unless they prefer to remain anonymous.
