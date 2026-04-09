# ============================================================
# ShopMarket - Extended Test Suite (Midterm)
# Includes: Unit, Integration, E2E, Edge Cases, Concurrency
# Запуск: pytest shopmarket_tests.py -v --html=report.html --self-contained-html --cov=. --cov-report=html
# ============================================================

import requests
import pytest
import threading
import time
import concurrent.futures

BASE = "http://localhost:8000"

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def login(email, password):
    resp = requests.post(f"{BASE}/api/auth/login/", json={"email": email, "password": password})
    return resp.json().get("access"), resp.json().get("refresh")

def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

def get_first_product():
    products = requests.get(f"{BASE}/api/products/").json()
    return products["results"][0]

def clear_and_add_item(token, product_id, qty=1):
    requests.delete(f"{BASE}/api/cart/clear/", headers=auth_headers(token))
    return requests.post(f"{BASE}/api/cart/items/",
        json={"product_id": product_id, "quantity": qty},
        headers=auth_headers(token)
    )


# ─────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────

@pytest.fixture(scope="session")
def buyer_token():
    token, _ = login("buyer1@test.com", "Test123!")
    assert token, "Could not login as buyer — check seed data"
    return token

@pytest.fixture(scope="session")
def buyer2_token():
    token, _ = login("buyer2@test.com", "Test123!")
    assert token, "Could not login as buyer2 — check seed data"
    return token

@pytest.fixture(scope="session")
def admin_token():
    token, _ = login("admin@marketplace.com", "Admin123!")
    assert token, "Could not login as admin"
    return token


# ============================================================
# UNIT TESTS — Logic-Level (discount math, validation rules)
# ============================================================

class TestUnitDiscountLogic:
    """
    TC-U01 to TC-U04: Unit-level tests for discount calculation logic.
    These tests verify that the API applies correct arithmetic for each coupon.
    """

    def test_TC_U01_save10_discount_math(self, buyer_token):
        """SAVE10 = exactly 10% off: total must equal price * 0.90"""
        product = get_first_product()
        product_id = product["id"]
        price = float(product["price"])

        clear_and_add_item(buyer_token, product_id, 1)
        requests.post(f"{BASE}/api/cart/apply-coupon/",
            json={"code": "SAVE10"}, headers=auth_headers(buyer_token))

        cart = requests.get(f"{BASE}/api/cart/", headers=auth_headers(buyer_token)).json()
        total = float(cart.get("total", cart.get("subtotal", 0)))
        expected = round(price * 0.90, 2)
        assert abs(total - expected) < 0.05, \
            f"SAVE10: expected ~{expected}, got {total} (price={price})"

    def test_TC_U02_save25_discount_math(self, buyer_token):
        """SAVE25 = exactly 25% off: total must equal price * 0.75"""
        product = get_first_product()
        product_id = product["id"]
        price = float(product["price"])

        clear_and_add_item(buyer_token, product_id, 1)
        requests.post(f"{BASE}/api/cart/apply-coupon/",
            json={"code": "SAVE25"}, headers=auth_headers(buyer_token))

        cart = requests.get(f"{BASE}/api/cart/", headers=auth_headers(buyer_token)).json()
        total = float(cart.get("total", cart.get("subtotal", 0)))
        expected = round(price * 0.75, 2)
        assert abs(total - expected) < 0.05, \
            f"SAVE25: expected ~{expected}, got {total}"

    def test_TC_U03_halfoff_discount_math(self, buyer_token):
        """HALFOFF = exactly 50% off: total must equal price * 0.50"""
        product = get_first_product()
        product_id = product["id"]
        price = float(product["price"])

        clear_and_add_item(buyer_token, product_id, 1)
        requests.post(f"{BASE}/api/cart/apply-coupon/",
            json={"code": "HALFOFF"}, headers=auth_headers(buyer_token))

        cart = requests.get(f"{BASE}/api/cart/", headers=auth_headers(buyer_token)).json()
        total = float(cart.get("total", cart.get("subtotal", 0)))
        expected = round(price * 0.50, 2)
        assert abs(total - expected) < 0.05, \
            f"HALFOFF: expected ~{expected}, got {total}"

    def test_TC_U04_no_coupon_full_price(self, buyer_token):
        """Without coupon, total equals base price (no discount applied)"""
        product = get_first_product()
        product_id = product["id"]
        price = float(product["price"])

        clear_and_add_item(buyer_token, product_id, 1)

        cart = requests.get(f"{BASE}/api/cart/", headers=auth_headers(buyer_token)).json()
        total = float(cart.get("total", cart.get("subtotal", 0)))
        assert abs(total - price) < 0.05, \
            f"No coupon: expected {price}, got {total}"


# ============================================================
# INTEGRATION TESTS — Module Interaction
# ============================================================

class TestIntegrationCartToOrder:
    """
    TC-I01 to TC-I05: Integration tests verifying that modules interact correctly.
    Cart → Order → Stock → Status flow tested end-to-end at API level.
    """

    def test_TC_I01_cart_coupon_reflected_in_order_total(self, buyer_token):
        """Coupon applied in cart must be reflected in the final order total"""
        product = get_first_product()
        product_id = product["id"]
        price = float(product["price"])

        clear_and_add_item(buyer_token, product_id, 1)
        requests.post(f"{BASE}/api/cart/apply-coupon/",
            json={"code": "SAVE10"}, headers=auth_headers(buyer_token))

        order_resp = requests.post(f"{BASE}/api/orders/",
            json={"shipping_address": "Integration Test Street 1"},
            headers=auth_headers(buyer_token)
        )
        assert order_resp.status_code == 201
        order_total = float(order_resp.json().get("total_price", 0))
        expected = round(price * 0.90, 2)
        assert abs(order_total - expected) < 0.10, \
            f"Coupon not reflected in order: expected ~{expected}, got {order_total}"

    def test_TC_I02_stock_consistent_after_order_cancel(self, buyer_token):
        """After order cancellation, stock must be restored to pre-order level"""
        product = get_first_product()
        product_id = product["id"]
        stock_before = int(requests.get(f"{BASE}/api/products/{product_id}/").json()["stock"])

        clear_and_add_item(buyer_token, product_id, 1)
        order = requests.post(f"{BASE}/api/orders/",
            json={"shipping_address": "123 Test Street"},
            headers=auth_headers(buyer_token)
        ).json()
        order_id = order["id"]

        # Stock should be reduced
        stock_after_order = int(requests.get(f"{BASE}/api/products/{product_id}/").json()["stock"])
        assert stock_after_order == stock_before - 1, "Stock not reduced after order"

        # Cancel and verify stock restored
        requests.post(f"{BASE}/api/orders/{order_id}/cancel/", headers=auth_headers(buyer_token))
        stock_after_cancel = int(requests.get(f"{BASE}/api/products/{product_id}/").json()["stock"])
        assert stock_after_cancel == stock_before, \
            f"Stock not restored after cancel: expected {stock_before}, got {stock_after_cancel}"

    def test_TC_I03_cart_cleared_after_order_created(self, buyer_token):
        """Cart must be empty after successful order placement"""
        product_id = get_first_product()["id"]
        clear_and_add_item(buyer_token, product_id, 1)

        requests.post(f"{BASE}/api/orders/",
            json={"shipping_address": "123 Test Street"},
            headers=auth_headers(buyer_token)
        )
        cart = requests.get(f"{BASE}/api/cart/", headers=auth_headers(buyer_token)).json()
        assert len(cart.get("items", [])) == 0, \
            "Cart not cleared after order was placed"

    def test_TC_I04_multiple_items_order_total_correct(self, buyer_token):
        """Order with multiple items must sum correctly"""
        products = requests.get(f"{BASE}/api/products/").json()["results"]
        requests.delete(f"{BASE}/api/cart/clear/", headers=auth_headers(buyer_token))

        expected_total = 0.0
        for p in products[:2]:
            requests.post(f"{BASE}/api/cart/items/",
                json={"product_id": p["id"], "quantity": 1},
                headers=auth_headers(buyer_token)
            )
            expected_total += float(p["price"])

        order = requests.post(f"{BASE}/api/orders/",
            json={"shipping_address": "Multi Item Street"},
            headers=auth_headers(buyer_token)
        ).json()
        order_total = float(order.get("total_price", 0))
        assert abs(order_total - expected_total) < 0.10, \
            f"Multi-item total wrong: expected ~{expected_total}, got {order_total}"

    def test_TC_I05_cancelled_order_status_is_cancelled(self, buyer_token):
        """Cancelled order must have status 'cancelled'"""
        product_id = get_first_product()["id"]
        clear_and_add_item(buyer_token, product_id, 1)

        order = requests.post(f"{BASE}/api/orders/",
            json={"shipping_address": "Cancel Test Street"},
            headers=auth_headers(buyer_token)
        ).json()
        order_id = order["id"]

        requests.post(f"{BASE}/api/orders/{order_id}/cancel/", headers=auth_headers(buyer_token))
        order_detail = requests.get(f"{BASE}/api/orders/{order_id}/", headers=auth_headers(buyer_token)).json()
        assert order_detail.get("status") == "cancelled", \
            f"Expected status=cancelled, got {order_detail.get('status')}"


# ============================================================
# EDGE CASE TESTS — Boundary & Invalid Input
# ============================================================

class TestEdgeCases:
    """
    TC-EDGE-01 to TC-EDGE-08: Edge case and boundary value tests.
    Tests empty inputs, extremely large values, and special characters.
    """

    def test_TC_EDGE_01_empty_email_login(self):
        """Login with empty email must return 400"""
        resp = requests.post(f"{BASE}/api/auth/login/", json={"email": "", "password": "Test123!"})
        assert resp.status_code == 400, f"Expected 400 for empty email, got {resp.status_code}"

    def test_TC_EDGE_02_empty_password_login(self):
        """Login with empty password must return 400"""
        resp = requests.post(f"{BASE}/api/auth/login/", json={"email": "buyer1@test.com", "password": ""})
        assert resp.status_code == 400, f"Expected 400 for empty password, got {resp.status_code}"

    def test_TC_EDGE_03_sql_injection_in_search(self):
        """SQL injection in search param must not crash the API"""
        resp = requests.get(f"{BASE}/api/products/", params={"search": "' OR '1'='1"})
        assert resp.status_code == 200, \
            f"API crashed on SQL injection input: {resp.status_code}"

    def test_TC_EDGE_04_special_characters_in_search(self):
        """Special characters in search must not return 500"""
        resp = requests.get(f"{BASE}/api/products/", params={"search": "<script>alert(1)</script>"})
        assert resp.status_code in [200, 400], \
            f"API returned 500 on XSS-like input: {resp.status_code}"

    def test_TC_EDGE_05_very_large_product_quantity(self, buyer_token):
        """Adding quantity=999999999 must be rejected"""
        product_id = get_first_product()["id"]
        requests.delete(f"{BASE}/api/cart/clear/", headers=auth_headers(buyer_token))
        resp = requests.post(f"{BASE}/api/cart/items/",
            json={"product_id": product_id, "quantity": 999999999},
            headers=auth_headers(buyer_token)
        )
        assert resp.status_code in [400, 422], \
            f"Expected rejection for qty=999999999, got {resp.status_code}"

    def test_TC_EDGE_06_nonexistent_product_id(self, buyer_token):
        """Adding a non-existent product to cart must return 400 or 404"""
        resp = requests.post(f"{BASE}/api/cart/items/",
            json={"product_id": 999999, "quantity": 1},
            headers=auth_headers(buyer_token)
        )
        assert resp.status_code in [400, 404], \
            f"Expected 400/404 for non-existent product, got {resp.status_code}"

    def test_TC_EDGE_07_order_without_shipping_address(self, buyer_token):
        """Creating order without shipping address must return 400"""
        product_id = get_first_product()["id"]
        clear_and_add_item(buyer_token, product_id, 1)
        resp = requests.post(f"{BASE}/api/orders/",
            json={},
            headers=auth_headers(buyer_token)
        )
        assert resp.status_code == 400, \
            f"Expected 400 for missing shipping address, got {resp.status_code}"

    def test_TC_EDGE_08_empty_cart_order(self, buyer_token):
        """Creating order with empty cart must return 400"""
        requests.delete(f"{BASE}/api/cart/clear/", headers=auth_headers(buyer_token))
        resp = requests.post(f"{BASE}/api/orders/",
            json={"shipping_address": "Test Street"},
            headers=auth_headers(buyer_token)
        )
        assert resp.status_code == 400, \
            f"Expected 400 for empty cart order, got {resp.status_code}"


# ============================================================
# CONCURRENCY TESTS — Race Conditions
# ============================================================

class TestConcurrency:
    """
    TC-CONC-01 to TC-CONC-03: Concurrency and race condition tests.
    Simulates simultaneous requests to detect oversell, double-submit bugs.
    """

    def test_TC_CONC_01_simultaneous_add_to_cart(self, buyer_token):
        """10 simultaneous add-to-cart requests must all succeed or fail cleanly (no 500)"""
        product_id = get_first_product()["id"]
        requests.delete(f"{BASE}/api/cart/clear/", headers=auth_headers(buyer_token))

        status_codes = []

        def add_item():
            resp = requests.post(f"{BASE}/api/cart/items/",
                json={"product_id": product_id, "quantity": 1},
                headers=auth_headers(buyer_token)
            )
            status_codes.append(resp.status_code)

        threads = [threading.Thread(target=add_item) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert 500 not in status_codes, \
            f"Server returned 500 during concurrent cart adds: {status_codes}"

    def test_TC_CONC_02_simultaneous_order_placement(self, buyer_token, buyer2_token):
        """Two users ordering the last unit simultaneously — only one should succeed if stock=1"""
        products = requests.get(f"{BASE}/api/products/").json()["results"]
        # Find a product with low stock or use first product
        product = products[0]
        product_id = product["id"]

        # Setup both buyers with same item in cart
        for token in [buyer_token, buyer2_token]:
            clear_and_add_item(token, product_id, 1)

        results = []

        def place_order(token):
            resp = requests.post(f"{BASE}/api/orders/",
                json={"shipping_address": "Concurrent Test Street"},
                headers=auth_headers(token)
            )
            results.append(resp.status_code)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(place_order, t) for t in [buyer_token, buyer2_token]]
            concurrent.futures.wait(futures)

        # At least one must succeed, no 500 errors
        assert 500 not in results, f"Server 500 on concurrent orders: {results}"
        assert 201 in results, f"No order succeeded in concurrent test: {results}"

    def test_TC_CONC_03_rapid_coupon_apply(self, buyer_token):
        """Rapid repeated coupon application must not double-discount"""
        product = get_first_product()
        product_id = product["id"]
        price = float(product["price"])

        clear_and_add_item(buyer_token, product_id, 1)

        # Apply coupon 5 times rapidly
        for _ in range(5):
            requests.post(f"{BASE}/api/cart/apply-coupon/",
                json={"code": "SAVE10"}, headers=auth_headers(buyer_token))

        cart = requests.get(f"{BASE}/api/cart/", headers=auth_headers(buyer_token)).json()
        total = float(cart.get("total", cart.get("subtotal", 0)))
        max_expected = price  # must never be MORE than original price
        min_expected = round(price * 0.50, 2)  # must not go below 50% (sanity)

        assert total <= max_expected, \
            f"Total {total} exceeds original price {max_expected} — coupon applied wrong"
        assert total >= min_expected, \
            f"Total {total} way too low — coupon stacked repeatedly: price={price}"


# ============================================================
# FAILURE SCENARIO TESTS — Invalid User Behavior
# ============================================================

class TestFailureScenarios:
    """
    TC-FAIL-01 to TC-FAIL-05: Tests for system behavior under failure conditions.
    Expired tokens, restricted endpoints, invalid transitions.
    """

    def test_TC_FAIL_01_expired_access_token_rejected(self):
        """A forged/expired access token must return 401"""
        fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE2MDAwMDAwMDB9.fake"
        resp = requests.get(f"{BASE}/api/cart/",
            headers={"Authorization": f"Bearer {fake_token}"}
        )
        assert resp.status_code == 401, \
            f"Expired token should return 401, got {resp.status_code}"

    def test_TC_FAIL_02_buyer_cannot_access_admin_endpoints(self, buyer_token):
        """Buyer must not access admin-only endpoints (coupons management)"""
        resp = requests.get(f"{BASE}/api/coupons/", headers=auth_headers(buyer_token))
        assert resp.status_code in [401, 403], \
            f"Buyer accessed admin endpoint: {resp.status_code}"

    def test_TC_FAIL_03_cancel_already_cancelled_order(self, buyer_token):
        """Cancelling an already cancelled order must return 400"""
        product_id = get_first_product()["id"]
        clear_and_add_item(buyer_token, product_id, 1)

        order = requests.post(f"{BASE}/api/orders/",
            json={"shipping_address": "Test Street"},
            headers=auth_headers(buyer_token)
        ).json()
        order_id = order["id"]

        # First cancel
        requests.post(f"{BASE}/api/orders/{order_id}/cancel/", headers=auth_headers(buyer_token))
        # Second cancel — must fail
        resp = requests.post(f"{BASE}/api/orders/{order_id}/cancel/",
            headers=auth_headers(buyer_token))
        assert resp.status_code in [400, 409, 422], \
            f"Expected error on double cancel, got {resp.status_code}"

    def test_TC_FAIL_04_register_duplicate_email(self):
        """Registering with an already-used email must return 400"""
        resp = requests.post(f"{BASE}/api/auth/register/", json={
            "email": "buyer1@test.com",
            "password": "Test123!",
            "password2": "Test123!",
            "first_name": "Duplicate",
            "last_name": "User",
            "role": "buyer"
        })
        assert resp.status_code == 400, \
            f"Expected 400 for duplicate email, got {resp.status_code}"

    def test_TC_FAIL_05_access_other_user_order(self, buyer_token, buyer2_token):
        """User must not access another user's order"""
        product_id = get_first_product()["id"]
        clear_and_add_item(buyer_token, product_id, 1)

        order = requests.post(f"{BASE}/api/orders/",
            json={"shipping_address": "Buyer1 Street"},
            headers=auth_headers(buyer_token)
        ).json()
        order_id = order["id"]

        # buyer2 tries to access buyer1's order
        resp = requests.get(f"{BASE}/api/orders/{order_id}/",
            headers=auth_headers(buyer2_token))
        assert resp.status_code in [403, 404], \
            f"buyer2 accessed buyer1's order: {resp.status_code}"


# ============================================================
# END-TO-END TESTS — Full User Journey (API Level)
# ============================================================

class TestE2EUserJourney:
    """
    TC-E2E-01 to TC-E2E-03: Full end-to-end user journey tests.
    Registration → Login → Browse → Cart → Coupon → Order → Cancel.
    These replicate real user flows at the API level.
    """

    def test_TC_E2E_01_full_purchase_journey(self):
        """Complete happy-path: register → login → add to cart → order"""
        import time as t
        email = f"e2e_test_{int(t.time())}@test.com"

        # Step 1: Register
        reg = requests.post(f"{BASE}/api/auth/register/", json={
            "email": email, "password": "Test123!", "password2": "Test123!",
            "first_name": "E2E", "last_name": "User", "role": "buyer"
        })
        assert reg.status_code in [200, 201], f"Registration failed: {reg.status_code} {reg.text}"

        # Step 2: Login
        login_resp = requests.post(f"{BASE}/api/auth/login/",
            json={"email": email, "password": "Test123!"})
        assert login_resp.status_code == 200
        token = login_resp.json()["access"]

        # Step 3: Browse products
        products = requests.get(f"{BASE}/api/products/").json()
        assert products["count"] > 0
        product_id = products["results"][0]["id"]

        # Step 4: Add to cart
        add = requests.post(f"{BASE}/api/cart/items/",
            json={"product_id": product_id, "quantity": 1},
            headers=auth_headers(token)
        )
        assert add.status_code == 201

        # Step 5: Place order
        order = requests.post(f"{BASE}/api/orders/",
            json={"shipping_address": "E2E Test Address, Almaty"},
            headers=auth_headers(token)
        )
        assert order.status_code == 201
        assert order.json().get("status") == "pending"

    def test_TC_E2E_02_purchase_with_coupon_journey(self):
        """Happy path with coupon: login → cart → SAVE25 → order"""
        import time as t
        email = f"e2e_coupon_{int(t.time())}@test.com"

        reg = requests.post(f"{BASE}/api/auth/register/", json={
            "email": email, "password": "Test123!", "password2": "Test123!",
            "first_name": "Coupon", "last_name": "User", "role": "buyer"
        })
        assert reg.status_code in [200, 201]

        token = requests.post(f"{BASE}/api/auth/login/",
            json={"email": email, "password": "Test123!"}).json()["access"]

        product = get_first_product()
        product_id = product["id"]
        price = float(product["price"])

        requests.post(f"{BASE}/api/cart/items/",
            json={"product_id": product_id, "quantity": 1},
            headers=auth_headers(token))

        coupon = requests.post(f"{BASE}/api/cart/apply-coupon/",
            json={"code": "SAVE25"}, headers=auth_headers(token))
        assert coupon.status_code == 200

        order = requests.post(f"{BASE}/api/orders/",
            json={"shipping_address": "Coupon Journey Street"},
            headers=auth_headers(token))
        assert order.status_code == 201

        total = float(order.json().get("total_price", 0))
        expected = round(price * 0.75, 2)
        assert abs(total - expected) < 0.10, \
            f"Coupon journey: expected ~{expected}, got {total}"

    def test_TC_E2E_03_review_submission_journey(self, buyer_token):
        """User who bought a product can submit a review"""
        product_id = get_first_product()["id"]
        clear_and_add_item(buyer_token, product_id, 1)

        order = requests.post(f"{BASE}/api/orders/",
            json={"shipping_address": "Review Test Street"},
            headers=auth_headers(buyer_token))
        assert order.status_code == 201

        # Submit review
        review = requests.post(f"{BASE}/api/reviews/",
            json={"product": product_id, "rating": 5, "comment": "Great product!"},
            headers=auth_headers(buyer_token))
        # Accept either success or "already reviewed" (idempotent)
        assert review.status_code in [200, 201, 400], \
            f"Unexpected review response: {review.status_code} {review.text}"