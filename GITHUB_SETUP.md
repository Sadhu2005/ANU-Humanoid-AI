# GitHub Repository Setup & CI/CD Guide

## 📦 Repository Information

**Repository URL**: https://github.com/Sadhu2005/ANU-AI-Humanoid

**Access**: Public repository - anyone can view and contribute

---

## 🔧 CI/CD Configuration

### GitHub Actions Workflow

The project includes automated deployment via GitHub Actions:

**File**: `.github/workflows/deploy.yml`

**What it does**:
- Automatically deploys website to GitHub Pages
- Triggers on push to `main` branch
- Deploys `Anu-website/` directory
- Uses GitHub Pages for hosting

### How to Enable

1. **Enable GitHub Pages**:
   - Go to repository Settings
   - Navigate to Pages section
   - Select source: "GitHub Actions"
   - Save

2. **Push to Main Branch**:
   ```bash
   git add .
   git commit -m "Update website"
   git push origin main
   ```

3. **Automatic Deployment**:
   - GitHub Actions will automatically run
   - Website will be deployed to: `https://sadhu2005.github.io/ANU-AI-Humanoid/`

---

## 📁 .gitignore Configuration

The `.gitignore` file is configured to exclude:

### Excluded Files:
- ✅ Virtual environments (`venv/`, `.venv/`, `env/`)
- ✅ Python cache (`__pycache__/`, `*.pyc`)
- ✅ Environment variables (`.env`, `.env.local`)
- ✅ Database files (`*.db`, `*.sqlite`)
- ✅ Model files (`models/`, `*.pkl`, `*.pt`, `*.h5`)
- ✅ Logs (`logs/`, `*.log`)
- ✅ IDE files (`.vscode/`, `.idea/`)
- ✅ OS files (`.DS_Store`, `Thumbs.db`)
- ✅ Build files (`build/`, `dist/`)

### Included Files:
- ✅ Source code
- ✅ Documentation
- ✅ Configuration files (without secrets)
- ✅ Website files
- ✅ Requirements files

---

## 🚀 Pushing to GitHub

### Initial Setup

```bash
# Initialize git (if not already done)
git init

# Add remote repository
git remote add origin https://github.com/Sadhu2005/ANU-AI-Humanoid.git

# Verify remote
git remote -v
```

### Regular Push Workflow

```bash
# Check status
git status

# Add all changes
git add .

# Commit with message
git commit -m "Your commit message here"

# Push to main branch
git push origin main
```

### Branch Workflow (Recommended)

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "Add feature description"

# Push branch
git push origin feature/your-feature-name

# Create Pull Request on GitHub
# After PR is merged, it will auto-deploy
```

---

## 📋 Pre-Push Checklist

Before pushing to GitHub, ensure:

- [ ] All sensitive data is in `.gitignore`
- [ ] No API keys in code (use `.env` file)
- [ ] No large model files (use Git LFS if needed)
- [ ] Code is tested and working
- [ ] Documentation is updated
- [ ] Commit messages are clear

---

## 🔐 Security Best Practices

1. **Never commit**:
   - API keys
   - Passwords
   - Private keys
   - Personal information

2. **Use environment variables**:
   ```python
   import os
   API_KEY = os.getenv('API_KEY')
   ```

3. **Review before pushing**:
   ```bash
   git diff  # Check what will be committed
   git status  # Check file status
   ```

---

## 🌐 GitHub Pages URL

Once deployed, your website will be available at:

**Main Site**: `https://sadhu2005.github.io/ANU-AI-Humanoid/`

**Direct Links**:
- Homepage: `https://sadhu2005.github.io/ANU-AI-Humanoid/index.html`
- Architecture: `https://sadhu2005.github.io/ANU-AI-Humanoid/architecture.html`

---

## 📊 Repository Structure on GitHub

```
ANU-AI-Humanoid/
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD configuration
├── Anu-Server/                  # Server code
├── Anu-website/                 # Website (deployed to Pages)
├── humanoid-robot/              # Robot code
├── .gitignore                   # Git ignore rules
├── README.md                    # Main documentation
├── PROJECT_DOCUMENTATION.md    # Project docs
├── RESEARCH_DOCUMENTATION.md   # Research docs
├── PRODUCT_DOCUMENTATION.md    # Product docs
└── SETUP_GUIDE.md              # Setup guide
```

---

## 🔄 Updating Website

### Quick Update Process

1. **Edit files locally**
2. **Test changes**
3. **Commit and push**:
   ```bash
   git add Anu-website/
   git commit -m "Update website: add new features"
   git push origin main
   ```
4. **Wait for deployment** (usually 1-2 minutes)
5. **Check GitHub Actions** tab for deployment status

---

## 🐛 Troubleshooting

### Deployment Fails

1. Check GitHub Actions logs
2. Verify `.github/workflows/deploy.yml` syntax
3. Ensure `Anu-website/` directory exists
4. Check branch name (should be `main`)

### Website Not Updating

1. Clear browser cache
2. Check GitHub Pages settings
3. Verify deployment completed in Actions
4. Wait a few minutes for DNS propagation

### Large File Issues

If you need to include large files:
```bash
# Install Git LFS
git lfs install

# Track large files
git lfs track "*.mp4"
git lfs track "models/**"

# Commit .gitattributes
git add .gitattributes
git commit -m "Add Git LFS tracking"
```

---

## 📞 Support

For GitHub-related issues:
- Check GitHub Actions logs
- Review repository settings
- Contact: sadhuj2005@gmail.com

---

**Last Updated**: January 2025
**Status**: ✅ Ready for Deployment

