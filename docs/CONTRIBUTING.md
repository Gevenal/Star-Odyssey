# Contributing to Odyssey-7

Thank you for your interest in contributing to Odyssey-7! This guide will help you get started.

## 🤝 How to Contribute

### Reporting Bugs

Before creating a bug report:
1. Check existing [Issues](https://github.com/yourusername/odyssey-7/issues)
2. Update to the latest version
3. Collect relevant logs and screenshots

**Good bug report includes:**
- Clear, descriptive title
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python/Node version)
- Error messages/logs

### Suggesting Features

Feature requests are welcome! Please:
1. Check if it's already suggested
2. Explain the use case clearly
3. Describe expected behavior
4. Consider implementation impact

## 🔧 Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB & Redis running locally
- Gemini API key

### Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/odyssey-7.git
cd odyssey-7
git remote add upstream https://github.com/ORIGINAL_OWNER/odyssey-7.git
```

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Dev dependencies
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Environment Configuration

Copy `.env.example` to `.env` and configure:
- Gemini API key
- MongoDB/Redis URLs
- CORS origins

## 📝 Coding Standards

### Python (Backend)

**Style Guide**: PEP 8

```python
# Good
def process_action(action: PlayerAction, state: GameState) -> ActionResult:
    """Process player action and return result."""
    # Implementation
    pass

# Bad
def processAction(action,state):
    pass
```

**Type Hints**: Always use
```python
# Good
def get_npc(npc_id: str) -> Optional[NPCState]:
    pass

# Bad
def get_npc(npc_id):
    pass
```

**Docstrings**: Required for public functions
```python
def validate_action(action: PlayerAction) -> RuleResult:
    """
    Validate player action against game rules.

    Args:
        action: Player action to validate

    Returns:
        RuleResult with validation outcome

    Raises:
        ValueError: If action is malformed
    """
```

### TypeScript (Frontend)

**Style Guide**: Airbnb + Prettier

```typescript
// Good
interface GameProps {
  sessionId: string;
  onActionSubmit: (action: PlayerAction) => void;
}

export const GameComponent: React.FC<GameProps> = ({ sessionId, onActionSubmit }) => {
  // Implementation
};

// Bad
export const GameComponent = (props: any) => {
  // Implementation
};
```

**Component Structure**:
```typescript
// 1. Imports
import React from 'react';
import { useGameStore } from '@/stores/gameStore';

// 2. Types
interface Props {
  // ...
}

// 3. Component
export const Component: React.FC<Props> = ({ prop }) => {
  // 4. Hooks
  const store = useGameStore();

  // 5. Functions
  const handleClick = () => {
    // ...
  };

  // 6. Render
  return <div>...</div>;
};
```

## 🧪 Testing

### Writing Tests

**Backend:**
```python
# tests/test_feature.py
import pytest
from app.core.feature import feature_function

class TestFeature:
    def test_success_case(self, sample_game_state):
        """Test successful execution."""
        result = feature_function(sample_game_state)
        assert result.success
    
    def test_failure_case(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            feature_function(None)
```

**Frontend:**
```typescript
// components/__tests__/Component.test.tsx
import { render, screen } from '@testing-library/react';
import { Component } from '../Component';

describe('Component', () => {
  it('renders correctly', () => {
    render(<Component />);
    expect(screen.getByText('Expected')).toBeInTheDocument();
  });
});
```

### Running Tests

```bash
# Backend
cd backend
pytest                    # All tests
pytest tests/test_file.py # Specific file
pytest -v                 # Verbose
pytest --cov=app          # With coverage

# Frontend
cd frontend
npm test                  # All tests
npm test -- Component     # Specific component
```

### Test Coverage

Aim for >80% coverage on new code.

```bash
# Backend coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Frontend coverage
npm test -- --coverage
```

## 📦 Pull Request Process

### Before Submitting

1. **Create a branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make changes**
   - Follow coding standards
   - Add tests
   - Update documentation

3. **Run tests**
   ```bash
   pytest        # Backend
   npm test      # Frontend
   ```

4. **Run linters**
   ```bash
   black app/    # Format Python
   mypy app/     # Type check
   npm run lint  # Lint TypeScript
   ```

5. **Commit**
   ```bash
   git commit -m "feat: Add amazing feature"
   ```

### Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructure
- `test`: Add tests
- `chore`: Maintenance

**Examples:**
```
feat(ai): Add streaming narration support

Implement Server-Sent Events for real-time narration
delivery. Includes frontend EventSource integration.

Closes #123
```

```
fix(rules): Correct resource decay calculation

Resources were decaying twice per turn due to duplicate
call in turn processor.

Fixes #456
```

### Submitting PR

1. **Push changes**
   ```bash
   git push origin feature/amazing-feature
   ```

2. **Create PR** on GitHub with:
   - Clear title
   - Description of changes
   - Related issue numbers
   - Screenshots (if UI changes)

3. **PR Checklist**
   - [ ] Tests pass
   - [ ] Documentation updated
   - [ ] No linter errors
   - [ ] Commit messages follow convention
   - [ ] Changelog updated (if applicable)

### Review Process

1. Maintainer reviews code
2. Automated tests run
3. Changes requested if needed
4. Approval → Merge

## 🏗️ Architecture Guidelines

### Adding New Features

1. **Plan first**: Create issue to discuss approach
2. **Follow patterns**: Use existing code as reference
3. **Keep it simple**: Avoid over-engineering
4. **Document**: Add docstrings and comments

### Backend Structure

```python
# New API endpoint
# app/api/routes/feature.py
from fastapi import APIRouter

router = APIRouter()

@router.post("/feature")
async def feature_endpoint(data: FeatureRequest):
    """Feature endpoint."""
    pass

# Register in app/api/__init__.py
```

### Frontend Structure

```typescript
// New component
// src/components/feature/FeatureComponent.tsx
export const FeatureComponent: React.FC<Props> = () => {
  // Implementation
};

// New store
// src/stores/featureStore.ts
export const useFeatureStore = create<FeatureStore>((set) => ({
  // State and actions
}));
```

## 🎨 UI/UX Guidelines

### Design Principles

1. **Clarity**: Information hierarchy is clear
2. **Feedback**: User actions have immediate response
3. **Consistency**: Similar actions work similarly
4. **Accessibility**: Keyboard nav, screen readers

### Component Guidelines

- Use Tailwind utility classes
- Follow existing color scheme
- Ensure mobile responsiveness
- Add loading states
- Handle errors gracefully

### Color Palette

```css
--primary: #3b82f6    /* Blue */
--danger: #ef4444     /* Red */
--warning: #f59e0b    /* Yellow */
--success: #10b981    /* Green */
--bg-dark: #111827    /* Dark background */
--bg-panel: #1f2937   /* Panel background */
```

## 📋 Checklist Template

Use this for PRs:

```markdown
## Changes
- [ ] Feature 1
- [ ] Feature 2

## Testing
- [ ] Unit tests added
- [ ] Integration tests pass
- [ ] Manual testing complete

## Documentation
- [ ] Code comments added
- [ ] API docs updated
- [ ] README updated (if needed)

## Review
- [ ] Self-review completed
- [ ] Linter passes
- [ ] No console warnings
- [ ] Performance considered
```

## 🙋 Questions?

- **Discord**: [Join our server](#)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/odyssey-7/discussions)
- **Email**: maintainer@example.com

## 📜 Code of Conduct

Be respectful, inclusive, and professional. We're all here to build something cool together.

---

Thank you for contributing! 🚀
