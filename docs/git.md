# Git Guide — NextGenAlgo

A clear, repeatable workflow for working on **NextGenAlgo** with full Git history and GitHub backup.

---

## Repo Locations
- **Local repo (active):** `E:\NextGenAlgo_clean`
- **Old code folder (archive):** `E:\AdityaFin_NextGenAlgo_DPR`
- **Remote (GitHub):** `https://github.com/Mohith0505/NextGenAlgo.git`

> Always work from `E:\NextGenAlgo_clean` going forward.

---

## One‑Time Setup (already done)

### 1) Create a clean Git repository
```bat
cd /d E:\
mkdir NextGenAlgo_clean
cd NextGenAlgo_clean
git init
```

### 2) Copy the project files into the new repo
```bat
xcopy "E:\AdityaFin_NextGenAlgo_DPR\*" "E:\NextGenAlgo_clean\" /E /I /H /Y
```

### 3) Review what changed
```bat
git status
:: optional detailed view
git diff
```

### 4) Stage files
```bat
git add .
```

### 5) Set your Git identity (global, once per machine)
```bat
git config --global user.name "Mohith V"
git config --global user.email "Mohith0505@users.noreply.github.com"
```

### 6) Commit
```bat
git commit -m "Initial commit with existing project files"
```

### 7) Connect to GitHub and set default branch
```bat
git remote add origin https://github.com/Mohith0505/NextGenAlgo.git
git branch -M main
```

### 8) Push first time
```bat
git push -u origin main
```
- `-u` sets the upstream so future pushes can be just `git push`.
- You may be asked to authenticate in the browser on first push.

### 9) (Optional) Clean up the old folder
- Archive or delete `E:\AdityaFin_NextGenAlgo_DPR` to avoid confusion.

---

## Daily Workflow (repeat every time you work)
1. **Check status**
   ```bat
   git status
   ```
2. **Stage changes** (all or specific files)
   ```bat
   git add .
   :: or: git add path\to\file
   ```
3. **Commit with a clear message**
   ```bat
   git commit -m "Describe what changed"
   ```
4. **Pull before pushing** (keeps local in sync if others commit)
   ```bat
   git pull --rebase
   ```
5. **Push to GitHub**
   ```bat
   git push
   ```

> Tip: Commit small, logical units with meaningful messages.

---

## Branching & PRs (recommended for new features)
- **Create & switch to a new branch**
  ```bat
  git checkout -b feature/short-description
  ```
- **Work, then push the branch**
  ```bat
  git push -u origin feature/short-description
  ```
- **Open a Pull Request** on GitHub from your branch into `main`.
- **Update your branch with main** as needed:
  ```bat
  git checkout main
  git pull --rebase
  git checkout feature/short-description
  git rebase main
  ```

---

## Useful Commands
- Show remotes
  ```bat
  git remote -v
  ```
- Change remote URL
  ```bat
  git remote set-url origin https://github.com/Mohith0505/NextGenAlgo.git
  ```
- See commit history
  ```bat
  git log --oneline --graph --decorate --all
  ```
- Undo staged file
  ```bat
  git restore --staged path\to\file
  ```
- Discard local changes to a file (careful!)
  ```bat
  git checkout -- path\to\file
  ```

---

## .gitignore (keep noise out of Git)
Create a `.gitignore` file in the repo root and add entries like:
```
# OS
Thumbs.db
.DS_Store

# Node / frontend
node_modules/
.build/
dist/

# Python
__pycache__/
*.pyc
.venv/

# Env & secrets
.env
.env.local

# Logs
*.log
```
> Adjust based on the tech stack in this project.

---

## Troubleshooting
- **"Author identity unknown" on commit**
  ```bat
  git config --global user.name "Mohith V"
  git config --global user.email "Mohith0505@users.noreply.github.com"
  ```
- **"remote origin already exists"**
  ```bat
  git remote remove origin
  git remote add origin https://github.com/Mohith0505/NextGenAlgo.git
  ```
- **Authentication issues when pushing**
  - Make sure you’re signed into GitHub Desktop/CLI or use a Personal Access Token for HTTPS.
  - If prompted in the browser, complete the login/2FA.
- **Accidentally committed a secret**
  - Rotate the secret immediately.
  - Remove it from history using GitHub’s guide (BFG Repo-Cleaner or git filter-repo), then force push.
- **Large files (>100MB)**
  - Use [Git LFS](https://git-lfs.com/): `git lfs install` then `git lfs track "*.bin"` and commit `.gitattributes`.

---

## Quick Reference (cheat sheet)
```bat
:: status → stage → commit → pull → push
git status
git add .
git commit -m "message"
git pull --rebase
git push

:: new branch workflow
git checkout -b feature/x
:: work, add, commit
git push -u origin feature/x
```

---

**Owner:** Mohith V  
**Last updated:** 2025-09-22
