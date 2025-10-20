import re
from django.conf import settings
from .models import PurchasingItem

def calculate_amount(items, discount):
    amount = 0
    
    for item_name in items:
        item = PurchasingItem.objects.filter(name=item_name).first()
        if not item:
            continue
        price = item.amount
        if discount and re.match(re.escape(discount.target), item.name):
            price *= (100 - discount.percentage) / 100
        amount += price
        
    return amount * 10