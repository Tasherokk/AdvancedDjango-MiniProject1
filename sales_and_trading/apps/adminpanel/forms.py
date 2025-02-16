from django import forms
from django.contrib.auth import get_user_model
from apps.products.models import Product, Category
from apps.sales.models import SalesOrder

User = get_user_model()

class UserForm(forms.ModelForm):
    """
    Form for creating/updating Users (in the custom admin panel).
    """
    password = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'password', 'profile_image']

    def save(self, commit=True):
        user = super().save(commit=False)
        # If password is provided, set it
        if self.cleaned_data['password']:
            user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class ProductForm(forms.ModelForm):
    """
    Form for creating/updating Products.
    """
    class Meta:
        model = Product
        fields = ['name', 'category', 'price', 'description', 'image']

class SalesOrderForm(forms.ModelForm):
    """
    Form for updating SalesOrder status, discount, etc.
    """
    class Meta:
        model = SalesOrder
        fields = ['status', 'discount_percent']


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']