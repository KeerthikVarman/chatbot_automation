---
trigger: always_on
---

## Dependency Management

Use only the packages, libraries, and frameworks already available in the project environment.

Before adding a dependency:
1. Inspect the existing environment.
2. Check requirements.txt, pyproject.toml, package.json, and lock files.
3. Reuse existing dependencies whenever possible.
4. Do not install new packages automatically.
5. Ask for approval before running pip install, npm install, pnpm add, yarn add, or other dependency installation commands.
6. Do not change or replace existing frameworks without approval.
7. Keep dependency versions compatible with the existing project.