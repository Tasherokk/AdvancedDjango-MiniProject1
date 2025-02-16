from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages

from .forms import RegisterForm, LoginForm, OrderForm
from apps.sales.models import SalesOrder, SalesOrderItem
from apps.products.models import Product
from django.utils import timezone
from django.http import HttpResponse, HttpResponseForbidden
from apps.analytics.tasks import generate_report_synchronously

from .forms import TraderProductForm
from apps.products.models import Product

from .forms import TradingOrderForm, TransactionForm
from apps.trading.models import Order, Transaction
from apps.trading.utils import attempt_to_match_order
from django.core.cache import cache

from sales_and_trading.utils.pdf_utils import render_pdf, pdf_response
from apps.sales.models import SalesOrder, Invoice


def index_view(request):
    return render(request, 'frontend/index.html')

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Registration successful. Please log in.")
            return redirect('frontend:login')
    else:
        form = RegisterForm()
    return render(request, 'frontend/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            if user:
                login(request, user)
                messages.success(request, f"Welcome, {user.username}!")
                return redirect('frontend:index')
    else:
        form = LoginForm()
    return render(request, 'frontend/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('frontend:index')


@login_required
def product_list_view(request):
    """
    List all products in a user-friendly manner,
    with caching to reduce DB load.
    """

    # Attempt to get cached product list
    products = cache.get('cached_product_list')

    if products is None:
        # If not in cache, query from DB
        products = list(Product.objects.select_related('category').all())
        # Store in cache for 60 seconds
        cache.set('cached_product_list', products, timeout=60)

    return render(request, 'frontend/product_list.html', {'products': products})

@login_required
def create_order_view(request):
    """
    Creates a new SalesOrder with one SalesOrderItem.
    """
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data['product']
            quantity = form.cleaned_data['quantity']
            price = form.cleaned_data['price']
            # create the order
            order = SalesOrder.objects.create(customer=request.user, status='pending', discount_percent=0)
            # create the order item
            SalesOrderItem.objects.create(
                sales_order=order, product=product,
                quantity=quantity, price=price
            )
            messages.success(request, f"Order #{order.id} created successfully.")
            return redirect('frontend:my_orders')
    else:
        form = OrderForm()
    return render(request, 'frontend/create_order.html', {'form': form})

@login_required
def my_orders_view(request):
    """
    List all SalesOrders for the logged-in user.
    """
    orders = SalesOrder.objects.filter(customer=request.user).order_by('-created_at')
    return render(request, 'frontend/order_list.html', {'orders': orders})

@login_required
def order_detail_view(request, order_id):
    """
    View detail for a single SalesOrder that belongs to the logged-in user.
    """
    order = get_object_or_404(SalesOrder, id=order_id, customer=request.user)
    return render(request, 'frontend/order_detail.html', {'order': order})


@login_required
def analytics_view(request):
    """
    Only Admin/Staff can access. If method = POST, generate & return CSV.
    """
    if not (request.user.role == 'admin' or request.user.is_staff):
        return HttpResponseForbidden("You do not have permission to access analytics.")

    if request.method == 'POST':
        # Generate the CSV
        file_path = generate_report_synchronously()
        # Read file content to return as response
        with open(file_path, 'rb') as f:
            file_data = f.read()
        response = HttpResponse(file_data, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="analytics_report.csv"'
        return response

    # If GET, just show a page with a "Generate" button
    return render(request, 'frontend/analytics.html')


@login_required
def create_product_view(request):
    """
    Allows a Trader or Admin to create a Product from the frontend.
    """
    # Check user role
    if not (request.user.role == 'admin' or request.user.role == 'trader' or request.user.is_staff):
        return HttpResponseForbidden("You do not have permission to create products.")

    if request.method == 'POST':
        form = TraderProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            # Clear or rebuild the product cache
            cache.delete('cached_product_list')
            messages.success(request, "Product created successfully.")
            return redirect('frontend:product_list')
    else:
        form = TraderProductForm()

    return render(request, 'frontend/create_product.html', {'form': form})


@login_required
def update_product_view(request, product_id):
    """
    Allows a Trader or Admin to edit a Product from the frontend.
    """
    if not (request.user.role == 'admin' or request.user.role == 'trader' or request.user.is_staff):
        return HttpResponseForbidden("You do not have permission to edit products.")

    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = TraderProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully.")
            return redirect('frontend:product_list')
    else:
        form = TraderProductForm(instance=product)

    return render(request, 'frontend/update_product.html', {'form': form, 'product': product})



########################################
# ORDERS
########################################

@login_required
def create_trading_order_view(request):
    if request.method == 'POST':
        form = TradingOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()

            # Immediately attempt to match the newly created order
            attempt_to_match_order(order)

            messages.success(request, f"{order.order_type.capitalize()} order #{order.id} placed successfully.")
            return redirect('frontend:list_trading_orders')
    else:
        form = TradingOrderForm()
    return render(request, 'frontend/create_trading_order.html', {'form': form})

@login_required
def list_trading_orders_view(request):
    """
    Shows the logged-in user their own orders (active or otherwise).
    If you want admin/trader to see all orders, check user role.
    """
    # For example, only 'admin' or 'trader' can see all. Otherwise, user sees only their own:
    if request.user.role in ['admin', 'trader']:
        orders = Order.objects.select_related('product').all().order_by('-created_at')
    else:
        orders = Order.objects.select_related('product').filter(user=request.user).order_by('-created_at')

    return render(request, 'frontend/list_trading_orders.html', {'orders': orders})

@login_required
def trading_order_detail_view(request, order_id):
    """
    Shows detail for a single Order (including its transactions).
    Ensures the user has permission to see it (owner or admin/trader).
    """
    order = get_object_or_404(Order, id=order_id)
    if order.user != request.user and request.user.role not in ['admin', 'trader']:
        return HttpResponseForbidden("You don't have permission to view this order.")

    return render(request, 'frontend/trading_order_detail.html', {'order': order})

########################################
# TRANSACTIONS
########################################

@login_required
def create_transaction_view(request):
    """
    Manually create a transaction for an existing order.
    Usually done automatically by matching logic in real trading systems.
    """
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save()
            messages.success(request, f"Transaction #{transaction.id} created for Order #{transaction.order.id}.")
            return redirect('frontend:list_transactions')
    else:
        form = TransactionForm()
    return render(request, 'frontend/create_transaction.html', {'form': form})

@login_required
def list_transactions_view(request):
    """
    Lists transactions. If you want only the user's own transactions, filter by order__user = request.user.
    Or if admin/trader can see all, do a role check.
    """
    if request.user.role in ['admin', 'trader']:
        transactions = Transaction.objects.select_related('order').all().order_by('-executed_at')
    else:
        # For normal customers, list only transactions of their orders
        transactions = Transaction.objects.select_related('order').filter(order__user=request.user).order_by('-executed_at')

    return render(request, 'frontend/list_transactions.html', {'transactions': transactions})




@login_required
def generate_invoice_frontend_view(request, order_id):
    """
    Generates (or retrieves) an Invoice for the given SalesOrder,
    then returns a PDF file as a download.
    Only the Customer who owns the order, or an Admin/Sales role, can do this.
    """
    # 1) Fetch the SalesOrder
    sales_order = get_object_or_404(SalesOrder, id=order_id)

    # 2) Check permissions: is user the order's customer, or has role admin/sales?
    user_role = request.user.role if hasattr(request.user, 'role') else 'customer'
    if request.user != sales_order.customer and user_role not in ['admin', 'sales']:
        return HttpResponseForbidden("You do not have permission to generate an invoice for this order.")

    # 3) Check if an Invoice already exists
    try:
        invoice = sales_order.invoice
    except Invoice.DoesNotExist:
        # If not, create one
        invoice = Invoice.objects.create(sales_order=sales_order)

    # 4) Render the PDF using your invoice_template.html
    context = {
        'invoice': invoice,
        'date': timezone.now()  # optional if you want current date in context
    }
    pdf_content = render_pdf('invoice_template.html', context_dict=context)

    # 5) Return as a downloadable PDF
    filename = f"invoice_{invoice.id}.pdf"
    return pdf_response(pdf_content, filename=filename)