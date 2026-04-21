"""
mutation_tests.py — ShopMarket
Тесты специально написаны для мутационного тестирования.
Запускать из корня проекта: pytest mutation_tests.py -v

Эти тесты нацелены на три файла с мутациями:
  - apps/orders/serializers.py   (calculate_discount)
  - apps/orders/views.py         (CancelOrderView, OrderListCreateView)
  - apps/products/views.py       (AddCartItemView)
"""

import requests

BASE = "http://localhost:8000"

# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────

def login(email="buyer1@test.com", password="Test123!"):
    r = requests.post(f"{BASE}/api/auth/login/", json={"email": email, "password": password})
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()["access"]

def auth_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def clear_cart(token):
    requests.delete(f"{BASE}/api/cart/clear/", headers=auth_headers(token))

def add_to_cart(token, product_id, quantity=1):
    return requests.post(
        f"{BASE}/api/cart/items/",
        json={"product_id": product_id, "quantity": quantity},
        headers=auth_headers(token),
    )

def place_order(token):
    return requests.post(
        f"{BASE}/api/orders/",
        json={"shipping_address": "Mutation Test Street 1"},
        headers=auth_headers(token),
    )

def get_product_stock(token, product_id):
    r = requests.get(f"{BASE}/api/products/{product_id}/", headers=auth_headers(token))
    return r.json().get("stock", 0)

def find_product_with_stock(token, min_stock=2):
    """Найти первый продукт с достаточным количеством на складе."""
    r = requests.get(f"{BASE}/api/products/", headers=auth_headers(token))
    body = r.json()
    products = body if isinstance(body, list) else body.get("results", [])
    for p in products:
        if p.get("stock", 0) >= min_stock and p.get("is_active", True):
            return p["id"], float(p["price"])
    return None, None


# ──────────────────────────────────────────────────────────────────
# MODULE 1: calculate_discount  (apps/orders/serializers.py)
# Мутации: изменение оператора *, /, константы 100, return Decimal("0.00")
# ──────────────────────────────────────────────────────────────────

class TestCalculateDiscount:
    """Цель: поймать мутации в calculate_discount()"""

    def test_save10_gives_exactly_10_percent(self):
        """SAVE10 должен давать ровно 10% скидки."""
        token = login()
        pid, price = find_product_with_stock(token)
        assert pid, "Нет продуктов со стоком"
        clear_cart(token)
        r = add_to_cart(token, pid, 1)
        assert r.status_code == 201, f"Add to cart failed: {r.text}"
        requests.post(f"{BASE}/api/cart/apply-coupon/",
                      json={"code": "SAVE10"}, headers=auth_headers(token))
        r = place_order(token)
        assert r.status_code == 201, f"Order failed: {r.text}"
        total = float(r.json()["total_price"])
        expected = round(price * 0.90, 2)
        assert abs(total - expected) < 0.02, f"SAVE10: expected {expected}, got {total}"

    def test_save25_gives_exactly_25_percent(self):
        """SAVE25 должен давать ровно 25% скидки."""
        token = login()
        pid, price = find_product_with_stock(token)
        assert pid, "Нет продуктов со стоком"
        clear_cart(token)
        r = add_to_cart(token, pid, 1)
        assert r.status_code == 201, f"Add to cart failed: {r.text}"
        requests.post(f"{BASE}/api/cart/apply-coupon/",
                      json={"code": "SAVE25"}, headers=auth_headers(token))
        r = place_order(token)
        assert r.status_code == 201, f"Order failed: {r.text}"
        total = float(r.json()["total_price"])
        expected = round(price * 0.75, 2)
        assert abs(total - expected) < 0.02, f"SAVE25: expected {expected}, got {total}"

    def test_halfoff_gives_exactly_50_percent(self):
        """HALFOFF должен давать ровно 50% скидки."""
        token = login()
        pid, price = find_product_with_stock(token)
        assert pid, "Нет продуктов со стоком"
        clear_cart(token)
        r = add_to_cart(token, pid, 1)
        assert r.status_code == 201, f"Add to cart failed: {r.text}"
        requests.post(f"{BASE}/api/cart/apply-coupon/",
                      json={"code": "HALFOFF"}, headers=auth_headers(token))
        r = place_order(token)
        assert r.status_code == 201, f"Order failed: {r.text}"
        total = float(r.json()["total_price"])
        expected = round(price * 0.50, 2)
        assert abs(total - expected) < 0.02, f"HALFOFF: expected {expected}, got {total}"

    def test_no_coupon_gives_full_price(self):
        """Без купона скидка = 0, итого = полная цена."""
        token = login()
        pid, price = find_product_with_stock(token)
        assert pid, "Нет продуктов со стоком"
        clear_cart(token)
        r = add_to_cart(token, pid, 1)
        assert r.status_code == 201, f"Add to cart failed: {r.text}"
        r = place_order(token)
        assert r.status_code == 201, f"Order failed: {r.text}"
        total = float(r.json()["total_price"])
        assert abs(total - price) < 0.02, f"No coupon: expected {price}, got {total}"

    def test_invalid_coupon_rejected(self):
        """Несуществующий купон должен вернуть 400."""
        token = login()
        r = requests.post(f"{BASE}/api/coupons/validate/",
                          json={"code": "FAKECODE999"}, headers=auth_headers(token))
        assert r.status_code == 400


# ──────────────────────────────────────────────────────────────────
# MODULE 2: OrderListCreateView._create_order  (apps/orders/views.py)
# Мутации: item.quantity > product.stock → >=, stock -= → +=, etc.
# ──────────────────────────────────────────────────────────────────

class TestOrderCreation:
    """Цель: поймать мутации в логике создания заказа."""

    def test_stock_decreases_after_order(self):
        """После заказа stock должен уменьшиться ровно на 1."""
        token = login()
        pid, _ = find_product_with_stock(token)
        assert pid, "Нет продуктов со стоком"
        stock_before = get_product_stock(token, pid)
        clear_cart(token)
        r = add_to_cart(token, pid, 1)
        assert r.status_code == 201
        r = place_order(token)
        assert r.status_code == 201
        stock_after = get_product_stock(token, pid)
        assert stock_after == stock_before - 1, \
            f"Stock: before={stock_before}, after={stock_after}"

    def test_order_total_equals_product_price(self):
        """Итого заказа без купона == цена товара."""
        token = login()
        pid, price = find_product_with_stock(token)
        assert pid, "Нет продуктов со стоком"
        clear_cart(token)
        r = add_to_cart(token, pid, 1)
        assert r.status_code == 201
        r = place_order(token)
        assert r.status_code == 201
        total = float(r.json()["total_price"])
        assert abs(total - price) < 0.02

    def test_empty_cart_order_rejected(self):
        """Заказ из пустой корзины должен вернуть 400."""
        token = login()
        clear_cart(token)
        r = place_order(token)
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"

    def test_oversell_blocked(self):
        """Количество больше стока должно быть отклонено."""
        token = login()
        pid, _ = find_product_with_stock(token)
        assert pid, "Нет продуктов со стоком"
        stock = get_product_stock(token, pid)
        clear_cart(token)
        r = add_to_cart(token, pid, stock + 100)
        assert r.status_code in [400, 422], \
            f"Oversell not blocked: {r.status_code} — {r.text}"

    def test_cart_cleared_after_order(self):
        """После успешного заказа корзина должна быть пустой."""
        token = login()
        pid, _ = find_product_with_stock(token)
        assert pid, "Нет продуктов со стоком"
        clear_cart(token)
        r = add_to_cart(token, pid, 1)
        assert r.status_code == 201
        r = place_order(token)
        assert r.status_code == 201
        cart = requests.get(f"{BASE}/api/cart/", headers=auth_headers(token)).json()
        items = cart.get("items", [])
        assert len(items) == 0, f"Cart not cleared: {items}"


# ──────────────────────────────────────────────────────────────────
# MODULE 3: CancelOrderView  (apps/orders/views.py)
# Мутации: order.status != "pending" → ==, stock += → -=
# ──────────────────────────────────────────────────────────────────

class TestOrderCancellation:
    """Цель: поймать мутации в логике отмены заказа."""

    def _create_pending_order(self, token):
        pid, _ = find_product_with_stock(token)
        assert pid, "Нет продуктов со стоком"
        clear_cart(token)
        r = add_to_cart(token, pid, 1)
        assert r.status_code == 201
        r = place_order(token)
        assert r.status_code == 201
        return r.json()["id"], pid

    def test_cancel_pending_order_succeeds(self):
        """Отмена pending заказа должна вернуть 200."""
        token = login()
        order_id, _ = self._create_pending_order(token)
        r = requests.post(f"{BASE}/api/orders/{order_id}/cancel/",
                          headers=auth_headers(token))
        assert r.status_code == 200, f"Cancel failed: {r.text}"

    def test_order_status_becomes_cancelled(self):
        """После отмены статус заказа должен быть 'cancelled'."""
        token = login()
        order_id, _ = self._create_pending_order(token)
        requests.post(f"{BASE}/api/orders/{order_id}/cancel/",
                      headers=auth_headers(token))
        r = requests.get(f"{BASE}/api/orders/{order_id}/", headers=auth_headers(token))
        assert r.json()["status"] == "cancelled"

    def test_stock_restored_after_cancel(self):
        """После отмены заказа stock должен вернуться к исходному."""
        token = login()
        pid, _ = find_product_with_stock(token)
        assert pid, "Нет продуктов со стоком"
        stock_before = get_product_stock(token, pid)
        clear_cart(token)
        r = add_to_cart(token, pid, 1)
        assert r.status_code == 201
        r = place_order(token)
        assert r.status_code == 201
        order_id = r.json()["id"]
        requests.post(f"{BASE}/api/orders/{order_id}/cancel/",
                      headers=auth_headers(token))
        stock_after = get_product_stock(token, pid)
        assert stock_after == stock_before, \
            f"Stock not restored: before={stock_before}, after={stock_after}"

    def test_double_cancel_rejected(self):
        """Повторная отмена уже отменённого заказа должна вернуть 400."""
        token = login()
        order_id, _ = self._create_pending_order(token)
        requests.post(f"{BASE}/api/orders/{order_id}/cancel/",
                      headers=auth_headers(token))
        r = requests.post(f"{BASE}/api/orders/{order_id}/cancel/",
                          headers=auth_headers(token))
        assert r.status_code in [400, 409, 422], \
            f"Double cancel should fail, got {r.status_code}"


# ──────────────────────────────────────────────────────────────────
# MODULE 4: AddCartItemView  (apps/products/views.py)
# Мутации: requested_qty < 1 → <=, new_total > product.stock → >=
# ──────────────────────────────────────────────────────────────────

class TestCartValidation:
    """Цель: поймать мутации в валидации корзины."""

    def test_add_valid_quantity_succeeds(self):
        """Добавление qty=1 должно вернуть 201."""
        token = login()
        pid, _ = find_product_with_stock(token)
        assert pid, "Нет продуктов со стоком"
        clear_cart(token)
        r = add_to_cart(token, pid, 1)
        assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"

    def test_quantity_zero_rejected(self):
        """qty=0 должен вернуть 400 или 422."""
        token = login()
        pid, _ = find_product_with_stock(token)
        assert pid
        r = add_to_cart(token, pid, 0)
        assert r.status_code in [400, 422], f"qty=0 should be rejected, got {r.status_code}"

    def test_negative_quantity_rejected(self):
        """qty=-1 должен вернуть 400 или 422."""
        token = login()
        pid, _ = find_product_with_stock(token)
        assert pid
        r = add_to_cart(token, pid, -1)
        assert r.status_code in [400, 422], f"qty=-1 should be rejected, got {r.status_code}"

    def test_quantity_exceeds_stock_rejected(self):
        """qty > stock должен вернуть 400."""
        token = login()
        pid, _ = find_product_with_stock(token)
        assert pid
        stock = get_product_stock(token, pid)
        clear_cart(token)
        r = add_to_cart(token, pid, stock + 100)
        assert r.status_code in [400, 422], \
            f"qty > stock should be rejected, got {r.status_code}: {r.text}"

    def test_nonexistent_product_rejected(self):
        """Несуществующий product_id должен вернуть 404."""
        token = login()
        r = add_to_cart(token, 999999, 1)
        assert r.status_code == 404, f"Expected 404, got {r.status_code}"

    def test_exact_stock_quantity_accepted(self):
        """qty == stock должен быть принят."""
        token = login()
        pid, _ = find_product_with_stock(token, min_stock=1)
        assert pid
        stock = get_product_stock(token, pid)
        if stock > 0:
            clear_cart(token)
            r = add_to_cart(token, pid, stock)
            assert r.status_code in [200, 201], \
                f"qty == stock should be accepted, got {r.status_code}: {r.text}"
