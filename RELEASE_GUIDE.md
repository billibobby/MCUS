# MCUS Release Guide

This guide helps you release new versions of MCUS to GitHub.

## 🚀 Release Process

### 1. Update Version Number

```bash
python update_version.py 1.1.0
```

This will automatically update the version number in:
- `src/update_checker.py`
- `README.md`

### 2. Test Your Changes

Make sure everything works:
```bash
python setup.py
python web_app.py --port 3000
```

### 3. Commit and Push Changes

```bash
git add .
git commit -m "Release version 1.1.0"
git push origin main
```

### 4. Create GitHub Release

1. Go to your GitHub repository
2. Click "Releases" in the right sidebar
3. Click "Create a new release"
4. Fill in the details:
   - **Tag version**: `v1.1.0`
   - **Release title**: `MCUS 1.1.0`
   - **Description**: Add your release notes

### 5. Push Tags

```bash
git push origin main --tags
```

## 📝 Release Notes Template

```markdown
## 🎉 MCUS 1.1.0 Release

### ✨ New Features
- Feature 1 description
- Feature 2 description

### 🔧 Improvements
- Improvement 1 description
- Improvement 2 description

### 🐛 Bug Fixes
- Fixed issue 1
- Fixed issue 2

### 📚 Documentation
- Updated documentation
- Added new guides

### 🔄 Breaking Changes
- Any breaking changes (if any)

---

**Download**: [MCUS 1.1.0](https://github.com/yourusername/MCUS/releases/tag/v1.1.0)

**Installation**: Follow the [Quick Start Guide](https://github.com/yourusername/MCUS#quick-start)
```

## 🔔 Update Notifications

When you create a GitHub release, users will automatically be notified:

1. **Automatic Detection**: MCUS checks for updates daily
2. **User Notification**: Users see a notification banner in the web interface
3. **Download Link**: Direct link to the GitHub release
4. **Release Notes**: Users can view release notes in the notification

## 📋 Pre-Release Checklist

- [ ] All features tested
- [ ] Documentation updated
- [ ] Version number updated
- [ ] Release notes written
- [ ] GitHub release created
- [ ] Tags pushed to GitHub

## 🎯 Version Numbering

Use semantic versioning (X.Y.Z):
- **X** - Major version (breaking changes)
- **Y** - Minor version (new features)
- **Z** - Patch version (bug fixes)

Examples:
- `1.0.0` - Initial release
- `1.1.0` - New features added
- `1.1.1` - Bug fixes
- `2.0.0` - Major update with breaking changes

## 🚨 Important Notes

1. **Update the version** in `src/update_checker.py` when releasing
2. **Create proper release notes** to help users understand changes
3. **Test thoroughly** before releasing
4. **Use semantic versioning** for consistent releases
5. **Push tags** so the update checker can find new releases

## 🔧 Troubleshooting

### Update Notifications Not Working
- Check that the GitHub repository name matches in `update_checker.py`
- Verify the release tag format (should be `v1.1.0`)
- Check the GitHub API rate limits

### Version Update Failed
- Make sure you're using the correct current version in `update_version.py`
- Check file permissions
- Verify file paths are correct

---

**Happy releasing! 🎉** 