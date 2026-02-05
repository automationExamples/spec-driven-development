import pytest
from playwright.sync_api import Page, expect





BASE_URL = "http://localhost:8000"

@pytest.fixture(scope="session")
def browser_context_args():
    return {"viewport": {"width": 1280, "height": 720}}

class TestBankingUI:
    def test_create_account(self, page: Page):
        page.goto(BASE_URL)
        page.fill("#accountName", "UI Test User")
        page.fill("#initialBalance", "500")
        page.click("button:has-text('Create')")
        expect(page.locator("#createResult")).to_contain_text("Account created")

    def test_view_account(self, page: Page):
        page.goto(BASE_URL)
        # Create account first
        page.fill("#accountName", "View Test")
        page.fill("#initialBalance", "200")
        page.click("button:has-text('Create')")
        page.wait_for_selector("#createResult:has-text('Account created')")
        
        # View account
        page.fill("#viewAccountId", "1")
        page.click("button:has-text('View')")
        expect(page.locator("#viewResult")).to_contain_text("Balance")

    def test_deposit(self, page: Page):
      page.goto(BASE_URL)
      # Create account
      page.fill("#accountName", "Deposit Test")
      page.fill("#initialBalance", "100")
      page.click("button:has-text('Create')")
      page.wait_for_selector("#createResult:has-text('Account created')")
      
      # Deposit
      page.fill("#depositAccountId", "1")
      page.fill("#depositAmount", "50")
      page.click("button:has-text('Deposit')")
      expect(page.locator("#depositResult")).to_contain_text("Deposited")

    def test_withdraw_insufficient_funds(self, page: Page):
      page.goto(BASE_URL)
      # Create account with low balance
      page.fill("#accountName", "Low Balance")
      page.fill("#initialBalance", "10")
      page.click("button:has-text('Create')")
      page.wait_for_selector("#createResult:has-text('Account created')")
      
      # Get the created account ID from the result
      result_text = page.locator("#createResult").text_content()
      # Extract ID from "Account created! ID: X, Name: ..."
      account_id = result_text.split("ID: ")[1].split(",")[0]
      
      # Try to withdraw more than balance
      page.fill("#withdrawAccountId", account_id)
      page.fill("#withdrawAmount", "100")
      page.click("button:has-text('Withdraw')")
      expect(page.locator("#withdrawResult")).to_contain_text("Insufficient funds")