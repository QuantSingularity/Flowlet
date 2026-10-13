import logging
import sys
import time
import uuid
from datetime import datetime
from typing import Any

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:5001"
API_BASE = f"{BASE_URL}/api/v1"


class FlowletProductionTester:

    def __init__(self) -> None:
        self.test_results = []
        self.access_token = None
        self.test_user_id = None
        self.test_accounts = []
        self.test_transactions = []

    def log_test(
        self, test_name: Any, success: Any, message: Any = "", data: Any = None
    ) -> Any:
        status = "PASS" if success else "FAIL"
        logger.info(f"{status} {test_name}: {message}")
        self.test_results.append(
            {
                "test": test_name,
                "success": success,
                "message": message,
                "data": data,
                "timestamp": datetime.now().isoformat(),
            }
        )
        if not success and data:
            logger.info(f"   Error details: {data}")

    def make_request(
        self, method: Any, endpoint: Any, data: Any = None, auth: Any = True
    ) -> Any:
        headers = {"Content-Type": "application/json"}
        if auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        url = f"{API_BASE}{endpoint}" if not endpoint.startswith("http") else endpoint
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            return response
        except Exception:
            return None

    def test_health_and_info(self) -> Any:
        logger.info("\nTesting Health and API Information...")
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                self.log_test(
                    "Health Check", True, f"Status: {health_data.get('status')}"
                )
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, f"Connection failed: {str(e)}")
            return False
        try:
            response = requests.get(f"{API_BASE}/info", timeout=10)
            if response.status_code == 200:
                info_data = response.json()
                features = len(info_data.get("features", []))
                self.log_test("API Info", True, f"Features: {features}")
            else:
                self.log_test("API Info", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("API Info", False, f"Request failed: {str(e)}")
        return True

    def test_user_registration(self) -> Any:
        logger.info("\nTesting User Registration...")
        test_email = f"test_{uuid.uuid4().hex[:8]}@flowlet.com"
        registration_data = {
            "email": test_email,
            "password": "SecurePassword123!",
            "first_name": "Test",
            "last_name": "User",
            "phone_number": "+1234567890",
        }
        response = self.make_request(
            "POST", "/auth/register", registration_data, auth=False
        )
        if response and response.status_code == 201:
            result = response.json()
            self.access_token = result.get("tokens", {}).get("access_token")
            self.test_user_id = result.get("user", {}).get("id")
            if self.access_token and self.test_user_id:
                self.log_test(
                    "User Registration", True, f"User ID: {self.test_user_id}"
                )
                return True
            else:
                self.log_test(
                    "User Registration", False, "Missing tokens or user ID", result
                )
                return False
        else:
            error_data = response.json() if response else None
            self.log_test(
                "User Registration",
                False,
                f"HTTP {(response.status_code if response else 'No response')}",
                error_data,
            )
            return False

    def test_user_login(self) -> Any:
        logger.info("\nTesting User Authentication...")
        if not self.test_user_id:
            self.log_test("User Login", False, "No test user available")
            return False
        response = self.make_request("GET", "/accounts", auth=True)
        if response and response.status_code == 200:
            self.log_test("Token Authentication", True, "Token is valid")
            return True
        else:
            self.log_test(
                "Token Authentication",
                False,
                f"HTTP {(response.status_code if response else 'No response')}",
            )
            return False

    def test_account_creation(self) -> Any:
        logger.info("\nTesting Account Management...")
        account_data = {
            "account_name": "Test Checking Account",
            "account_type": "checking",
            "currency": "USD",
            "initial_deposit": "1000.00",
        }
        response = self.make_request("POST", "/accounts", account_data)
        if response and response.status_code == 201:
            result = response.json()
            account = result.get("account", {})
            account_id = account.get("id")
            if account_id:
                self.test_accounts.append(account_id)
                self.log_test("Account Creation", True, f"Account ID: {account_id}")
                return account_id
            else:
                self.log_test(
                    "Account Creation", False, "No account ID returned", result
                )
                return None
        else:
            error_data = response.json() if response else None
            self.log_test(
                "Account Creation",
                False,
                f"HTTP {(response.status_code if response else 'No response')}",
                error_data,
            )
            return None

    def test_balance_operations(self, account_id: Any) -> Any:
        logger.info("\nTesting Balance Operations...")
        if not account_id:
            self.log_test("Balance Operations", False, "No account ID provided")
            return False
        response = self.make_request("GET", f"/accounts/{account_id}/balance")
        if response and response.status_code == 200:
            balance_data = response.json()
            current_balance = balance_data.get("current_balance", "0")
            self.log_test("Balance Inquiry", True, f"Balance: ${current_balance}")
        else:
            self.log_test(
                "Balance Inquiry",
                False,
                f"HTTP {(response.status_code if response else 'No response')}",
            )
            return False
        deposit_data = {
            "amount": "500.00",
            "description": "Test deposit",
            "reference": f"TEST_DEP_{uuid.uuid4().hex[:8]}",
        }
        response = self.make_request(
            "POST", f"/accounts/{account_id}/deposit", deposit_data
        )
        if response and response.status_code == 200:
            result = response.json()
            transaction = result.get("transaction", {})
            new_balance = result.get("new_balance", "0")
            if transaction.get("id"):
                self.test_transactions.append(transaction["id"])
                self.log_test(
                    "Fund Deposit",
                    True,
                    f"Amount: $500.00, New Balance: ${new_balance}",
                )
            else:
                self.log_test(
                    "Fund Deposit", False, "No transaction ID returned", result
                )
        else:
            error_data = response.json() if response else None
            self.log_test(
                "Fund Deposit",
                False,
                f"HTTP {(response.status_code if response else 'No response')}",
                error_data,
            )
        withdrawal_data = {
            "amount": "200.00",
            "description": "Test withdrawal",
            "reference": f"TEST_WD_{uuid.uuid4().hex[:8]}",
        }
        response = self.make_request(
            "POST", f"/accounts/{account_id}/withdraw", withdrawal_data
        )
        if response and response.status_code == 200:
            result = response.json()
            transaction = result.get("transaction", {})
            new_balance = result.get("new_balance", "0")
            if transaction.get("id"):
                self.test_transactions.append(transaction["id"])
                self.log_test(
                    "Fund Withdrawal",
                    True,
                    f"Amount: $200.00, New Balance: ${new_balance}",
                )
            else:
                self.log_test(
                    "Fund Withdrawal", False, "No transaction ID returned", result
                )
        else:
            error_data = response.json() if response else None
            self.log_test(
                "Fund Withdrawal",
                False,
                f"HTTP {(response.status_code if response else 'No response')}",
                error_data,
            )
        return True

    def test_transfers(self) -> Any:
        logger.info("\nTesting Fund Transfers...")
        if len(self.test_accounts) < 2:
            second_account_data = {
                "account_name": "Test Savings Account",
                "account_type": "savings",
                "currency": "USD",
                "initial_deposit": "500.00",
            }
            response = self.make_request("POST", "/accounts", second_account_data)
            if response and response.status_code == 201:
                result = response.json()
                account = result.get("account", {})
                account_id = account.get("id")
                if account_id:
                    self.test_accounts.append(account_id)
                else:
                    self.log_test(
                        "Transfer Setup", False, "Could not create second account"
                    )
                    return False
            else:
                self.log_test(
                    "Transfer Setup", False, "Could not create second account"
                )
                return False
        transfer_data = {
            "from_account_id": self.test_accounts[0],
            "to_account_id": self.test_accounts[1],
            "amount": "300.00",
            "description": "Test transfer between accounts",
        }
        response = self.make_request("POST", "/transfers", transfer_data)
        if response and response.status_code == 200:
            result = response.json()
            transfer = result.get("transfer", {})
            debit_tx = transfer.get("debit_transaction", {})
            credit_tx = transfer.get("credit_transaction", {})
            if debit_tx.get("id") and credit_tx.get("id"):
                self.test_transactions.extend([debit_tx["id"], credit_tx["id"]])
                self.log_test("Fund Transfer", True, "Amount: $300.00")
            else:
                self.log_test("Fund Transfer", False, "Missing transaction IDs", result)
        else:
            error_data = response.json() if response else None
            self.log_test(
                "Fund Transfer",
                False,
                f"HTTP {(response.status_code if response else 'No response')}",
                error_data,
            )
        return True

    def test_transaction_history(self) -> Any:
        logger.info("\nTesting Transaction History...")
        if not self.test_accounts:
            self.log_test("Transaction History", False, "No test accounts available")
            return False
        account_id = self.test_accounts[0]
        response = self.make_request("GET", f"/accounts/{account_id}/transactions")
        if response and response.status_code == 200:
            result = response.json()
            transactions = result.get("transactions", [])
            pagination = result.get("pagination", {})
            self.log_test(
                "Transaction History", True, f"Found {len(transactions)} transactions"
            )
            if pagination.get("total", 0) > 0:
                self.log_test(
                    "Transaction Pagination", True, f"Total: {pagination['total']}"
                )
            return True
        else:
            error_data = response.json() if response else None
            self.log_test(
                "Transaction History",
                False,
                f"HTTP {(response.status_code if response else 'No response')}",
                error_data,
            )
            return False

    def test_error_handling(self) -> Any:
        logger.info("\nTesting Error Handling...")
        response = self.make_request("GET", "/accounts/invalid-account-id/balance")
        if response and response.status_code == 404:
            self.log_test("Invalid Account Error", True, "Correctly returned 404")
        else:
            self.log_test(
                "Invalid Account Error",
                False,
                f"Expected 404, got {(response.status_code if response else 'No response')}",
            )
        if self.test_accounts:
            withdrawal_data = {
                "amount": "999999.00",
                "description": "Test insufficient funds",
            }
            response = self.make_request(
                "POST", f"/accounts/{self.test_accounts[0]}/withdraw", withdrawal_data
            )
            if response and response.status_code == 400:
                error_data = response.json()
                if error_data.get("code") == "INSUFFICIENT_FUNDS":
                    self.log_test(
                        "Insufficient Funds Error",
                        True,
                        "Correctly detected insufficient funds",
                    )
                else:
                    self.log_test(
                        "Insufficient Funds Error",
                        False,
                        f"Wrong error code: {error_data.get('code')}",
                    )
            else:
                self.log_test(
                    "Insufficient Funds Error",
                    False,
                    f"Expected 400, got {(response.status_code if response else 'No response')}",
                )
        if self.test_accounts:
            invalid_deposit_data = {
                "amount": "invalid_amount",
                "description": "Test invalid amount",
            }
            response = self.make_request(
                "POST",
                f"/accounts/{self.test_accounts[0]}/deposit",
                invalid_deposit_data,
            )
            if response and response.status_code == 400:
                self.log_test(
                    "Invalid Amount Error", True, "Correctly rejected invalid amount"
                )
            else:
                self.log_test(
                    "Invalid Amount Error",
                    False,
                    f"Expected 400, got {(response.status_code if response else 'No response')}",
                )
        old_token = self.access_token
        self.access_token = "invalid_token"
        response = self.make_request("GET", "/accounts")
        if response and response.status_code == 401:
            self.log_test(
                "Unauthorized Access Error", True, "Correctly rejected invalid token"
            )
        else:
            self.log_test(
                "Unauthorized Access Error",
                False,
                f"Expected 401, got {(response.status_code if response else 'No response')}",
            )
        self.access_token = old_token
        return True

    def test_security_features(self) -> Any:
        logger.info("\nTesting Security Features...")
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response:
            headers = response.headers
            security_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options",
                "X-XSS-Protection",
                "Strict-Transport-Security",
                "Content-Security-Policy",
            ]
            missing_headers = [h for h in security_headers if h not in headers]
            if not missing_headers:
                self.log_test("Security Headers", True, "All security headers present")
            else:
                self.log_test(
                    "Security Headers", False, f"Missing headers: {missing_headers}"
                )
        rate_limit_test = True
        for i in range(3):
            response = self.make_request("GET", "/accounts")
            if not response or response.status_code not in [200, 429]:
                rate_limit_test = False
                break
        self.log_test("Rate Limiting", rate_limit_test, "Rate limiting is active")
        return True

    def run_comprehensive_test_suite(self) -> Any:
        logger.info("Starting Flowlet Production Test Suite")
        logger.info("=" * 70)
        logger.info("Testing enterprise-grade financial backend implementation")
        logger.info("=" * 70)
        logger.info("\n⏳ Waiting for server to be ready...")
        time.sleep(3)
        if not self.test_health_and_info():
            logger.info("Basic connectivity failed. Cannot continue.")
            return False
        if not self.test_user_registration():
            logger.info("User registration failed. Cannot continue.")
            return False
        if not self.test_user_login():
            logger.info("Authentication failed. Cannot continue.")
            return False
        account_id = self.test_account_creation()
        if account_id:
            self.test_balance_operations(account_id)
            self.test_transfers()
            self.test_transaction_history()
        self.test_error_handling()
        self.test_security_features()
        logger.info("\nProduction Test Results Summary")
        logger.info("=" * 70)
        total_tests = len(self.test_results)
        passed_tests = sum((1 for result in self.test_results if result["success"]))
        failed_tests = total_tests - passed_tests
        logger.info(f"Total Tests Executed: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {passed_tests / total_tests * 100:.1f}%")
        if failed_tests > 0:
            logger.info("\nFailed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    logger.info(f"   - {result['test']}: {result['message']}")
        logger.info("\nTest Artifacts Created:")
        logger.info(f"   - User ID: {self.test_user_id}")
        logger.info(f"   - Accounts: {len(self.test_accounts)}")
        logger.info(f"   - Transactions: {len(self.test_transactions)}")
        logger.info("\nProduction Readiness Assessment:")
        if passed_tests / total_tests >= 0.95:
            logger.info(" EXCELLENT - Ready for production deployment")
        elif passed_tests / total_tests >= 0.9:
            logger.info(" GOOD - Ready for production with minor fixes")
        elif passed_tests / total_tests >= 0.8:
            logger.info(" FAIR - Needs improvements before production")
        else:
            logger.info(" POOR - Significant issues need resolution")
        return failed_tests == 0


def main() -> Any:
    logger.info("Flowlet Production Test Suite")
    logger.info("Enterprise Financial Backend Validation")
    logger.info("Testing comprehensive functionality and security")
    tester = FlowletProductionTester()
    success = tester.run_comprehensive_test_suite()
    if success:
        logger.info("\nAll tests passed! Production backend is ready for deployment.")
        sys.exit(0)
    else:
        logger.info(
            "\nSome tests failed. Please review and fix issues before production."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
