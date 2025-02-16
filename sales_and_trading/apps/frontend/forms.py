from django import forms
from django.contrib.auth import get_user_model, authenticate
from apps.trading.models import Order, Transaction
from apps.products.models import Product

User = get_user_model()

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'customer'  # default role is customer
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if not user:
            raise forms.ValidationError("Invalid username or password.")
        self.user_cache = user
        return cleaned_data

    def get_user(self):
        return self.user_cache


class OrderForm(forms.Form):
    """
    For demonstration: allow user to pick a product, quantity, price, discount, etc.
    This is a simplified approach. We'll create a SalesOrder with one item.
    """
    product = forms.ModelChoiceField(queryset=Product.objects.all())
    quantity = forms.IntegerField(min_value=1)
    price = forms.DecimalField(min_value=0, decimal_places=2)


class TraderProductForm(forms.ModelForm):
    """
    A form that Traders or Admins can use to create/edit Products.
    """
    class Meta:
        model = Product
        fields = ['name', 'category', 'price', 'description', 'image']


class TradingOrderForm(forms.ModelForm):
    """
    Form to place or edit an Order (buy/sell).
    """
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        required=True
    )
    order_type = forms.ChoiceField(
        choices=[('buy', 'Buy'), ('sell', 'Sell')],
        required=True
    )

    class Meta:
        model = Order
        fields = ['product', 'order_type', 'quantity', 'price']


class TransactionForm(forms.ModelForm):
    """
    Form to manually create a Transaction for an existing Order.
    """
    class Meta:
        model = Transaction
        fields = ['order', 'executed_price', 'quantity']