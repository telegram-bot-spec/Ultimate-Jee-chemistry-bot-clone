# Security Policy

## 🔒 Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | ✅ Yes             |
| < 1.0   | ❌ No              |

## 🚨 Reporting a Vulnerability

We take the security of Ultimate Chemistry Bot seriously. If you discover a security vulnerability, please follow these steps:

### 1. **DO NOT** Open a Public Issue
Security vulnerabilities should not be disclosed publicly until they have been addressed.

### 2. Report Privately
Send a detailed report to the project maintainers via:
- GitHub Security Advisory (preferred)
- Direct message to maintainers
- Email (if provided in profile)

### 3. Include in Your Report
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)
- Your contact information

### 4. Response Timeline
- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Varies by severity
  - Critical: 24-48 hours
  - High: 7 days
  - Medium: 30 days
  - Low: 90 days

## 🛡️ Security Best Practices

### For Users
1. **Never share your bot token publicly**
2. **Use environment variables** for all sensitive data
3. **Rotate API keys** regularly (every 90 days)
4. **Enable 2FA** on your GitHub and Railway accounts
5. **Monitor bot logs** for suspicious activity
6. **Use latest version** of the bot

### For Developers
1. **Never commit secrets** to the repository
2. **Use `.gitignore`** to exclude sensitive files
3. **Validate all inputs** from users
4. **Sanitize file uploads** to prevent injection
5. **Use parameterized queries** (if database added)
6. **Keep dependencies updated**
7. **Follow principle of least privilege**

## 🔐 Known Security Considerations

### API Keys
- Bot token has full access to your Telegram bot
- Gemini API keys can incur costs if abused
- **Mitigation**: Use environment variables, rotate regularly

### User Uploads
- Users can upload malicious images
- **Mitigation**: File type validation, size limits, sandboxed processing

### PDF Generation
- WeasyPrint executes HTML/CSS
- **Mitigation**: Input sanitization, no external resources

### Rate Limiting
- Bot can be spammed
- **Mitigation**: Implement per-user rate limits (TODO)

## 🔄 Security Updates

Security updates will be announced via:
- GitHub Security Advisories
- CHANGELOG.md
- Repository releases

## 📝 Security Checklist

### Deployment Checklist
- [ ] All secrets in environment variables
- [ ] `.env` file in `.gitignore`
- [ ] Bot token rotated after public exposure
- [ ] Railway variables set (not hardcoded)
- [ ] Logs don't expose sensitive data
- [ ] Dependencies up to date
- [ ] HTTPS used for all connections

### Code Review Checklist
- [ ] No hardcoded credentials
- [ ] Input validation present
- [ ] Error messages don't leak info
- [ ] File operations are safe
- [ ] External libraries are trusted
- [ ] Logging excludes sensitive data

## 🏆 Hall of Fame

We appreciate security researchers who help keep this project safe. Contributors who report valid security issues will be acknowledged here (with permission):

- *Your name could be here!*

## 📞 Contact

For security concerns, please use GitHub's private vulnerability reporting feature or contact the maintainers directly.

---

**Remember**: Security is everyone's responsibility. If you see something, say something!
