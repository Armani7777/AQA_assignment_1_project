"""
run_mutations.py — ShopMarket Mutation Testing Script
Works both locally (via Docker) and in CI/CD (GitHub Actions).

Usage:
  Local:  docker exec -w /app backend python run_mutations.py
  CI/CD:  cd backend && python run_mutations.py
"""

import subprocess
import sys
import os

# ── Detect environment ────────────────────────────────────────────
# In CI: files are at backend/apps/...  (run from repo root or backend/)
# In Docker: files are at /app/apps/... (run from /app)

def find_base_path():
    """Find the backend base path where apps/ directory lives."""
    candidates = [
        os.path.dirname(os.path.abspath(__file__)),  # same dir as this script
        "/app",                                        # Docker container
        os.path.join(os.getcwd(), "backend"),          # CI from repo root
        os.getcwd(),                                   # CI from backend/
    ]
    for path in candidates:
        if os.path.isdir(os.path.join(path, "apps", "orders")):
            return path
    return None

BASE = find_base_path()
if not BASE:
    print("ERROR: Cannot find apps/orders directory. Run from backend/ or /app")
    sys.exit(1)

print(f"Using base path: {BASE}")

# ── Find test file ────────────────────────────────────────────────
def find_test_file():
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "mutation_tests.py"),
        os.path.join(os.getcwd(), "mutation_tests.py"),
        os.path.join(os.getcwd(), "..", "mutation_tests.py"),
        "/app/mutation_tests.py",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None

TEST_FILE = find_test_file()
if not TEST_FILE:
    print("ERROR: Cannot find mutation_tests.py")
    sys.exit(1)

print(f"Using test file: {TEST_FILE}")

# ── Mutation definitions ──────────────────────────────────────────
mutations = [
    (
        "apps/orders/serializers.py",
        '/ Decimal("100")',
        '* Decimal("100")',
        "Discount: / replaced with *"
    ),
    (
        "apps/orders/serializers.py",
        'return Decimal("0.00")',
        'return Decimal("999.00")',
        "Discount: return 0.00 replaced with 999.00"
    ),
    (
        "apps/orders/views.py",
        "if item.quantity > product.stock:",
        "if item.quantity >= product.stock:",
        "Order: > replaced with >="
    ),
    (
        "apps/orders/views.py",
        "product.stock -= item.quantity",
        "product.stock += item.quantity",
        "Order: -= replaced with +="
    ),
    (
        "apps/orders/views.py",
        'if order.status != "pending":',
        'if order.status == "pending":',
        "Cancel: != replaced with =="
    ),
    (
        "apps/orders/views.py",
        "if not cart.items.exists():\n            return Response({\"detail\": \"Cart is empty.\"}, status=status.HTTP_400_BAD_REQUEST)",
        "if False:\n            return Response({\"detail\": \"Cart is empty.\"}, status=status.HTTP_400_BAD_REQUEST)",
        "Order: empty cart check removed (function removal)"
    ),
    (
        "apps/products/views.py",
        "if requested_qty < 1:",
        "if requested_qty <= 1:",
        "Cart: < replaced with <="
    ),
    (
        "apps/products/views.py",
        "if new_total > product.stock:",
        "if new_total >= product.stock:",
        "Cart: > replaced with >="
    ),
]

# ── Run mutations ─────────────────────────────────────────────────
results = []

for rel_path, original, mutant_code, desc in mutations:
    full_path = os.path.join(BASE, rel_path)

    if not os.path.isfile(full_path):
        results.append((desc, "SKIP — file not found"))
        print(f"SKIP (not found): {full_path}")
        continue

    content = open(full_path, encoding="utf-8").read()

    if original not in content:
        results.append((desc, "SKIP — pattern not found"))
        print(f"SKIP (pattern not found): {desc}")
        print(f"  Looking for: {repr(original[:60])}")
        continue

    # Apply mutation
    open(full_path, "w", encoding="utf-8").write(
        content.replace(original, mutant_code, 1)
    )

    # Run tests
    r = subprocess.run(
        [sys.executable, "-m", "pytest", TEST_FILE, "-x", "-q", "--tb=no"],
        capture_output=True, text=True
    )

    # Restore original
    open(full_path, "w", encoding="utf-8").write(content)

    status = "KILLED" if r.returncode != 0 else "SURVIVED"
    results.append((desc, status))
    print(f"{status}: {desc}")

# ── Summary ───────────────────────────────────────────────────────
print()
print("=== MUTATION SCORE ===")
killed   = sum(1 for _, s in results if s == "KILLED")
survived = sum(1 for _, s in results if s == "SURVIVED")
total    = sum(1 for _, s in results if not s.startswith("SKIP"))

if total > 0:
    score = round(killed / total * 100)
    print(f"Killed:   {killed}/{total} = {score}%")
    print(f"Survived: {survived}/{total}")
else:
    print("No mutants executed.")

print()
for desc, status in results:
    print(f"  {status}: {desc}")
