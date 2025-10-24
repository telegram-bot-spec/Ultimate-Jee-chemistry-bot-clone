# Contributing to Ultimate Chemistry Bot

Thank you for considering contributing! This document provides guidelines for contributing to the project.

## 🤝 How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Screenshots if applicable
- Bot logs (remove sensitive info)

### Suggesting Enhancements

Open an issue with:
- Clear description of the enhancement
- Use case and benefits
- Possible implementation approach

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 Code Guidelines

### Python Style

- Follow PEP 8
- Use meaningful variable names
- Add docstrings for functions
- Keep functions focused and small

### Example:
```python
async def enhance_image(image_bytes: bytes) -> bytes:
    """
    Enhance image quality for better analysis.
    
    Args:
        image_bytes: Raw image data
        
    Returns:
        Enhanced image bytes
    """
    # Implementation
```

### Commit Messages

Format: `[Type] Brief description`

Types:
- `[Feature]` - New feature
- `[Fix]` - Bug fix
- `[Docs]` - Documentation
- `[Refactor]` - Code refactoring
- `[Test]` - Testing
- `[Perf]` - Performance improvement

Examples:
```
[Feature] Add support for organic chemistry diagrams
[Fix] Resolve PDF generation error for long solutions
[Docs] Update deployment guide with troubleshooting
```

## 🧪 Testing

Before submitting PR:
- Test locally with sample images
- Verify PDF generation works
- Check error handling
- Test with multiple API keys
- Ensure no hardcoded tokens

## 📚 Areas for Contribution

### High Priority
- [ ] Add more chemistry knowledge sources
- [ ] Improve PDF formatting
- [ ] Add support for handwritten equations
- [ ] Implement user feedback system
- [ ] Add statistics tracking

### Medium Priority
- [ ] Add support for more languages
- [ ] Implement caching improvements
- [ ] Add unit tests
- [ ] Improve error messages
- [ ] Add progress indicators

### Low Priority
- [ ] Add dark mode PDFs
- [ ] Implement custom templates
- [ ] Add voice note support
- [ ] Create web dashboard

## 🔒 Security

- Never commit API keys or tokens
- Use environment variables
- Report security issues privately
- Follow OWASP guidelines

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## ❓ Questions?

Open an issue or reach out to maintainers.

Thank you for contributing! 🎉
