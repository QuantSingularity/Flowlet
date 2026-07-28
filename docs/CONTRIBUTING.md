# Contributing to Flowlet

Thank you for your interest in contributing to Flowlet! This guide will help you get started with contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Submitting Changes](#submitting-changes)
- [Documentation](#documentation)

## Code of Conduct

By participating in this project, you agree to:

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Git

### Fork and Clone

```bash
# Fork the repository on GitHub first
git clone https://github.com/quantsingularity/Flowlet.git
cd Flowlet

# Add upstream remote
git remote add upstream https://github.com/quantsingularity/Flowlet.git
```

### Setup Development Environment

```bash
# Install dependencies
make setup

# Or manually:
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cd ../web-frontend
npm install
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Your Changes

Follow our code style guidelines (see below).

### 3. Write Tests

All new features must include tests:

```bash
# Backend tests
cd backend
pytest tests/unit/test_your_feature.py

# Frontend tests
cd web-frontend
npm test -- your-component.test.tsx
```

### 4. Run Quality Checks

```bash
# Format code
make format

# Run linting
make lint

# Run all tests
make test
```

### 5. Commit Your Changes

Follow conventional commit format:

```bash
git commit -m "feat: add new wallet feature"
git commit -m "fix: resolve payment processing bug"
git commit -m "docs: update API documentation"
```

**Commit Types**:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build process or auxiliary tool changes

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Style Guidelines

### Python (Backend)

**Style**: PEP 8 with Black formatter

```python
# Good
def create_wallet(user_id: str, currency: str) -> Wallet:
    """Create a new wallet for the user.

    Args:
        user_id: Unique user identifier
        currency: ISO 4217 currency code

    Returns:
        Created wallet instance
    """
    wallet = Wallet(user_id=user_id, currency=currency)
    db.session.add(wallet)
    db.session.commit()
    return wallet
```

**Key Rules**:

- Use type hints for function parameters and returns
- Write docstrings for all public functions/classes
- Maximum line length: 100 characters
- Use meaningful variable names
- Follow Flask best practices

**Formatting**:

```bash
cd backend
black src/
flake8 src/ --max-line-length=100
```

### TypeScript (Frontend)

**Style**: Airbnb style guide with Prettier

```typescript
// Good
interface WalletProps {
  walletId: string;
  onUpdate: (wallet: Wallet) => void;
}

export const WalletComponent: React.FC<WalletProps> = ({
  walletId,
  onUpdate
}) => {
  const [wallet, setWallet] = useState<Wallet | null>(null);

  useEffect(() => {
    fetchWallet(walletId).then(setWallet);
  }, [walletId]);

  return <div>{wallet?.balance}</div>;
};
```

**Key Rules**:

- Use TypeScript for all new code
- Prefer functional components with hooks
- Use proper TypeScript types (avoid `any`)
- Extract reusable logic into custom hooks
- Follow React best practices

**Formatting**:

```bash
cd web-frontend
npm run format
npm run lint
```

### File Organization

```
backend/src/
├── routes/           # API endpoints (one file per resource)
├── models/           # Database models
├── services/         # Business logic
├── utils/            # Helper functions
└── tests/            # Test files mirror src structure

web-frontend/
├── components/       # Reusable UI components
├── pages/            # Page-level components
├── hooks/            # Custom React hooks
├── lib/              # Utilities and API clients
└── types/            # TypeScript type definitions
```

## Testing Requirements

### Backend Testing

**Required Coverage**: Minimum 80%

```bash
# Run tests with coverage
cd backend
pytest --cov=src --cov-report=html tests/

# View coverage report
open htmlcov/index.html
```

**Test Structure**:

```python
# tests/unit/test_wallet.py
import pytest
from src.models.wallet import Wallet
from src.services.wallet_service import WalletService

class TestWalletService:
    def test_create_wallet_success(self, db_session):
        """Test successful wallet creation."""
        service = WalletService(db_session)
        wallet = service.create_wallet(
            user_id="user_123",
            currency="USD"
        )
        assert wallet.currency == "USD"
        assert wallet.balance == 0

    def test_create_wallet_invalid_currency(self, db_session):
        """Test wallet creation with invalid currency."""
        service = WalletService(db_session)
        with pytest.raises(ValueError):
            service.create_wallet(
                user_id="user_123",
                currency="INVALID"
            )
```

### Frontend Testing

**Required**: Tests for all components and hooks

```bash
# Run tests
cd web-frontend
npm test

# Run with coverage
npm test -- --coverage
```

**Test Structure**:

```typescript
// __tests__/WalletComponent.test.tsx
import { render, screen } from '@testing-library/react';
import { WalletComponent } from '../components/WalletComponent';

describe('WalletComponent', () => {
  it('renders wallet balance', () => {
    render(<WalletComponent walletId="123" />);
    expect(screen.getByText(/balance/i)).toBeInTheDocument();
  });

  it('handles loading state', () => {
    render(<WalletComponent walletId="123" />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});
```

### Integration Tests

Test complete workflows:

```python
# tests/integration/test_payment_flow.py
def test_complete_payment_flow(client, auth_headers):
    """Test end-to-end payment processing."""
    # Create wallet
    wallet_response = client.post(
        '/api/v1/accounts/wallets',
        json={'currency': 'USD'},
        headers=auth_headers
    )
    assert wallet_response.status_code == 201

    # Deposit funds
    # ...

    # Make payment
    # ...

    # Verify transaction
    # ...
```

## Submitting Changes

### Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated (if needed)
- [ ] Commit messages follow conventional format
- [ ] PR description explains changes clearly
- [ ] No merge conflicts with main branch

### Pull Request Template

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests pass locally
```

### Review Process

1. **Automated Checks**: CI/CD runs tests and linting
2. **Code Review**: At least one maintainer reviews
3. **Feedback**: Address review comments
4. **Approval**: Maintainer approves PR
5. **Merge**: Maintainer merges to main

## Documentation

### When to Update Docs

Update documentation when:

- Adding new API endpoints
- Changing existing functionality
- Adding new configuration options
- Fixing bugs that affect user behavior

### Documentation Files

| File                     | When to Update            |
| ------------------------ | ------------------------- |
| `docs/API.md`            | New/changed API endpoints |
| `docs/CONFIGURATION.md`  | New environment variables |
| `docs/FEATURE_MATRIX.md` | New features              |
| `docs/examples/`         | New usage patterns        |

### Writing Documentation

**Good Documentation**:

````markdown
## Create Wallet

Create a new wallet for the authenticated user.

**Endpoint**: `POST /api/v1/accounts/wallets`

**Parameters**:

| Name     | Type   | Required | Description                      |
| -------- | ------ | -------- | -------------------------------- |
| currency | string | Yes      | ISO 4217 currency code           |
| type     | string | No       | Wallet type (personal, business) |

**Example**:

\```bash
curl -X POST http://localhost:5000/api/v1/accounts/wallets \
-H "Authorization: Bearer TOKEN" \
-H "Content-Type: application/json" \
-d '{"currency": "USD"}'
\```
````

## Community

### Getting Help

- **GitHub Issues**: Report bugs or request features
- **Discussions**: Ask questions or discuss ideas
- **Pull Requests**: Submit code changes

### Communication

- Be clear and concise
- Provide context and examples
- Be patient and respectful

## License

By contributing to Flowlet, you agree that your contributions will be licensed under the MIT License.
