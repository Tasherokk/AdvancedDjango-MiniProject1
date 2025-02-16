# apps/trading/utils.py

from django.db import transaction
from apps.trading.models import Order, Transaction
from decimal import Decimal

def attempt_to_match_order(new_order):
    """
    A naive matching engine:
    1. If new_order is a buy, look for an active sell order
       with the same product, price <= new_order.price, and the same quantity.
    2. If new_order is a sell, look for an active buy order
       with price >= new_order.price, same product, same quantity.
    3. If found, create a Transaction for new_order and also create a matching transaction for the matched order (or just update status).
    4. Mark both orders as 'closed'.
    """

    if new_order.status != 'active':
        return  # Only match if new_order is active

    # Opposite order_type
    opposite_type = 'sell' if new_order.order_type == 'buy' else 'buy'

    # Construct a query for potential matches
    # We'll do an EXACT quantity match for simplicity
    # You might want partial fills in real life
    qs = Order.objects.filter(
        product=new_order.product,
        order_type=opposite_type,
        status='active',
        quantity=new_order.quantity
    )

    # Price condition:
    if new_order.order_type == 'buy':
        # Looking for sells with price <= new_order.price
        qs = qs.filter(price__lte=new_order.price)
        # We'll pick the "best" price (lowest) => order_by('price', 'created_at')
        qs = qs.order_by('price', 'created_at')
    else:
        # new_order is sell => look for buys with price >= sell price
        qs = qs.filter(price__gte=new_order.price)
        # We'll pick the "best" price (highest) => order_by('-price', 'created_at')
        qs = qs.order_by('-price', 'created_at')

    match = qs.first()
    if not match:
        return  # No match found

    # Found a match, create transactions
    with transaction.atomic():
        # We'll define the executed_price (could be midpoint or the match's price)
        if new_order.order_type == 'buy':
            # Let's just use the match's price (the seller's ask)
            executed_price = match.price
        else:
            # new_order is sell => let's use the match's price (the buyer's bid)
            executed_price = match.price

        # Or you could do something like:
        # executed_price = (new_order.price + match.price) / Decimal('2.0')

        # We'll assume the quantity is exactly the same
        matched_quantity = new_order.quantity

        # 1) Create a transaction for the new_order
        Transaction.objects.create(
            order=new_order,
            executed_price=executed_price,
            quantity=matched_quantity
        )
        # 2) Create a transaction for the matched order
        Transaction.objects.create(
            order=match,
            executed_price=executed_price,
            quantity=matched_quantity
        )

        # 3) Mark both orders as closed
        new_order.status = 'closed'
        new_order.save()
        match.status = 'closed'
        match.save()
