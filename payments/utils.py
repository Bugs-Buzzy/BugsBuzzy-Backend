import re
import json
from django.conf import settings
from .models import PurchasingItem

def calculate_amount(items, discount):
    amount = 0
    applied = False
    
    for item_name in items:
        item = PurchasingItem.objects.filter(name=item_name).first()
        if not item:
            continue
        price = item.amount
        if discount and re.match(discount.target, item.name):
            price *= (100 - discount.percentage) / 100
            applied = True
        amount += price
        
    return amount * 10, applied


def apply_purchase(items_str):
    items = json.loads(items_str)
    
    for item_name in items:
        item = PurchasingItem.objects.filter(name=item_name).first()
        item.purchased_count += 1
        item.save()