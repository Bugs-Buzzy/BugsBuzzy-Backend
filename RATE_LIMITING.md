# Rate Limiting & Anti-Brute Force Protection

این مستندات توضیح می‌دهد که چگونه از حملات brute-force به کدهای تخفیف جلوگیری می‌شود.

## مشکل

بدون محدودیت، یک مهاجم می‌تواند:

1. هزاران درخواست `GET /payment/discount/` ارسال کند
2. کدهای تخفیف مختلف را امتحان کند (مثل: `SUMMER2025`, `DISCOUNT10`, `WELCOME`, ...)
3. کدهای معتبر را پیدا کند و از آن‌ها سوءاستفاده کند

## راه‌حل: دو Endpoint جداگانه

ما از دو endpoint جداگانه استفاده می‌کنیم:

### 1. GET /payment/price/ - محاسبه قیمت عادی (بدون rate limit)

این endpoint برای محاسبه قیمت **بدون کد تخفیف** استفاده می‌شود.

**ویژگی‌ها:**

- **هیچ محدودیتی ندارد** - می‌تواند بارها فراخوانی شود
- برای real-time price updates استفاده می‌شود
- وقتی کاربر checkbox ها را تغییر می‌دهد، قیمت به‌روز می‌شود

**مثال درخواست:**

```bash
GET /payment/price/?items=inperson&items=thursday_lunch
```

**مثال پاسخ:**

```json
{
  "amount": 350000
}
```

### 2. GET /payment/discount/ - اعمال کد تخفیف (با rate limit سخت)

این endpoint برای بررسی و اعمال کد تخفیف استفاده می‌شود.

**ویژگی‌ها:**

- **Rate limited: 10 requests per minute per user**
- فقط وقتی کاربر دکمه "اعمال" را می‌زند فراخوانی می‌شود
- جلوی brute-force attacks را می‌گیرد

**مثال درخواست:**

```bash
GET /payment/discount/?code=SUMMER2025&items=inperson&items=thursday_lunch
```

**مثال پاسخ موفق:**

```json
{
  "amount": 280000,
  "discount_applied": true,
  "discount_percentage": 20
}
```

**مثال پاسخ خطا (کد نامعتبر):**

```json
{
  "error": "Invalid discount code",
  "discount_applied": false
}
```

**مثال پاسخ خطا (rate limit):**

```json
{
  "detail": "Request was throttled. Expected available in 45 seconds."
}
```

## پیاده‌سازی Backend

### Throttling Class

**فایل:** `payments/throttling.py`

```python
class PriceCheckThrottle(UserRateThrottle):
    scope = 'price_check'
    rate = '10/min'  # 10 requests per minute per user
```

### Views

**فایل:** `payments/views.py`

```python
class PriceView(APIView):
    """محاسبه قیمت بدون کد تخفیف - بدون rate limit"""
    permission_classes = [IsAuthenticated, IsVerified, ProfileCompleted]
    
    def get(self, request):
        items = request.query_params.getlist("items")
        amount, _ = calculate_amount(items, None)
        return Response({"amount": int(amount)})


class DiscountView(APIView):
    """اعمال کد تخفیف - با rate limit سخت"""
    permission_classes = [IsAuthenticated, IsVerified, ProfileCompleted]
    throttle_classes = [PriceCheckThrottle]
    
    def get(self, request):
        code = request.query_params.get("code", "").strip()
        items = request.query_params.getlist("items")
        
        discount = DiscountCode.objects.filter(code__iexact=code.lower()).first()
        if not discount:
            return Response(
                {"error": "Invalid discount code", "discount_applied": False},
                status=404
            )
        
        amount, applied = calculate_amount(items, discount)
        return Response({
            "amount": int(amount),
            "discount_applied": applied,
            "discount_percentage": discount.percentage
        })
```

### URLs

**فایل:** `payments/urls.py`

```python
urlpatterns = [
    path("price/", views.PriceView.as_view(), name="price"),
    path("discount/", views.DiscountView.as_view(), name="discount"),
    path("pay/", views.PaymentView.as_view(), name="pay"),
]
```

## پیاده‌سازی Frontend

### Payment Service

**فایل:** `src/services/payments.service.ts`

```typescript
class PaymentsService {
  // بدون rate limit - برای real-time updates
  async getPrice(items: string[]): Promise<PriceResponse> {
    const params = new URLSearchParams();
    items.forEach(item => params.append('items', item));
    return apiClient.get(`/payment/price/?${params}`);
  }

  // با rate limit - فقط با کلیک دکمه
  async applyDiscount(code: string, items: string[]): Promise<DiscountResponse> {
    const params = new URLSearchParams();
    params.append('code', code);
    items.forEach(item => params.append('items', item));
    return apiClient.get(`/payment/discount/?${params}`);
  }
}
```

### Component Logic

```typescript
// محاسبه قیمت خودکار (بدون کد تخفیف)
useEffect(() => {
  if (stage === 'payment') {
    calculatePrice(); // فراخوانی GET /payment/price/
  }
}, [thursdayLunch, fridayLunch, stage]);

// اعمال کد تخفیف (با کلیک دکمه)
const handleApplyDiscount = async () => {
  try {
    const result = await paymentsService.applyDiscount(code, items);
    // GET /payment/discount/ - rate limited
    setCalculatedPrice(result.amount);
    setDiscountApplied(true);
  } catch (err) {
    if (err.response?.status === 429) {
      setError('تعداد درخواست‌های شما بیش از حد مجاز است');
    }
  }
};
```

## تست

### تست rate limiting

```bash
# ارسال 11 درخواست پشت سر هم به discount endpoint
for i in {1..11}; do
  curl "http://localhost:8000/payment/discount/?code=TEST${i}&items=inperson" \
    -H "Authorization: Bearer YOUR_TOKEN" \
    && echo " - Request $i"
done
```

درخواست یازدهم باید 429 Too Many Requests برگرداند.

### تست price endpoint (بدون limit)

```bash
# ارسال 100 درخواست - همه باید موفق باشند
for i in {1..100}; do
  curl "http://localhost:8000/payment/price/?items=inperson" \
    -H "Authorization: Bearer YOUR_TOKEN" \
    && echo " - Request $i"
done
```

همه درخواست‌ها باید موفق باشند.

## مزایا

1. **کاربر عادی:** هیچ محدودیتی برای تغییر item ها و محاسبه قیمت ندارد
2. **امنیت:** brute-force کدهای تخفیف غیرممکن است (فقط ۱۰ تلاش در دقیقه)
3. **UX بهتر:** قیمت به‌صورت real-time به‌روز می‌شود
4. **کاهش بار:** محدود کردن فقط endpoint حساس

## نکات امنیتی اضافی

1. **Case-insensitive:** کدهای تخفیف case-insensitive هستند
2. **Usage limit:** هر کد تخفیف می‌تواند `max_uses` داشته باشه
3. **Validity check:** `is_valid()` چک می‌کنه که کد منقضی نشده
4. **Target pattern:** کدها با regex فقط به item های خاص اعمال میشن

## توسعه آینده

1. **IP-based throttling:** محدودیت اضافی بر اساس IP
2. **CAPTCHA:** بعد از چند تلاش ناموفق
3. **Monitoring:** لاگ تلاش‌های مشکوک در پنل ادمین
4. **Adaptive rate:** کاهش rate برای رفتار مشکوک
