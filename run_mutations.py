import subprocess

mutations = [
    ('apps/orders/serializers.py', '/ Decimal("100")', '* Decimal("100")', 'Discount: / to *'),
    ('apps/orders/serializers.py', 'return Decimal("0.00")', 'return Decimal("999.00")', 'Discount: return 0 to 999'),
    ('apps/orders/views.py', 'if item.quantity > product.stock:', 'if item.quantity >= product.stock:', 'Order: > to >='),
    ('apps/orders/views.py', 'product.stock -= item.quantity', 'product.stock += item.quantity', 'Order: -= to +='),
    ('apps/orders/views.py', 'if order.status != "pending":', 'if order.status == "pending":', 'Cancel: != to =='),
    ('apps/products/views.py', 'if requested_qty < 1:', 'if requested_qty <= 1:', 'Cart: < to <='),
    ('apps/products/views.py', 'if new_total > product.stock:', 'if new_total >= product.stock:', 'Cart: > to >='),
]

results = []
for filepath, original, mutant_code, desc in mutations:
    path = '/app/' + filepath
    content = open(path).read()
    if original not in content:
        results.append((desc, 'SKIP'))
        print(f'SKIP (not found): {desc}')
        continue
    open(path,'w').write(content.replace(original, mutant_code, 1))
    r = subprocess.run(['python','-m','pytest','/app/mutation_tests.py','-x','-q','--tb=no'], capture_output=True, text=True, cwd='/app')
    open(path,'w').write(content)
    status = 'KILLED' if r.returncode != 0 else 'SURVIVED'
    results.append((desc, status))
    print(f'{status}: {desc}')

print()
print('=== MUTATION SCORE ===')
killed = sum(1 for _,s in results if s=='KILLED')
total = sum(1 for _,s in results if s!='SKIP')
print(f'Killed: {killed}/{total} = {round(killed/total*100)}%')
for desc, status in results:
    print(f'  {status}: {desc}')
