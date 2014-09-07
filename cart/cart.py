from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect

import decimal # not needed yet but we will later
import random

from models import CartItem
from catalog.models import Product


CART_ID_SESSION_KEY = 'cart_id'

def _cart_id(request):
  """Get the current user's cart id, sets new one if blank
  """
  if request.session.get(CART_ID_SESSION_KEY, '') == '':
    request.session[CART_ID_SESSION_KEY] = _generate_cart_id()
  return request.session[CART_ID_SESSION_KEY]


def _generate_cart_id():
  """Generates a unique id string for a cart
  """
  cart_id = ''
  characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890!@#$%^&*()'
  cart_id_length = 50

  # TODO(eso) there's got to be a better way to generate a random string of 50 characters
  for y in range(cart_id_length):
    cart_id += characters[random.randint(0, len(characters)-1)]

  return cart_id


def get_cart_items(request):
  """Return all items from the current user's cart
  """
  return CartItem.objects.filter(cart_id=_cart_id(request))


def cart_distinct_item_count(request):
  """Returns the total number of items in the user's cart
  """
  return get_cart_items(request).count()


def get_single_item(request, item_id):
  """Get a single item from the cart
  """
  return get_object_or_404(CartItem, id=item_id, cart_id=_cart_id(request))


def add_to_cart(request):
  """Add an item to the cart
  """
  postdata = request.POST.copy()

  # get product slug from post data, return blank if empty
  product_slug = postdata.get('product_slug', '')

  # get quantity added, return 1 if empty
  quantity = postdata.get('quantity', 1)

  # fetch the product or return a missing page error
  p = get_object_or_404(Product, slug=product_slug)

  # get products in cart
  cart_products = get_cart_items(request)
  product_in_cart = False

  # check to see if item is already in cart
  for cart_item in cart_products:
    if cart_item.product.id == p.id:
      # update the quantity if found
      cart_item.augment_quantity(quantity)
      product_in_cart = True

  if not product_in_cart:
    # create and save a new cart item
    ci = CartItem()
    ci.product = p
    ci.quantity = quantity
    ci.cart_id = _cart_id(request)
    ci.save()


def update_cart(request):
  """Update quantity for single item
  """
  postdata = request.POST.copy()
  item_id = postdata['item_id']
  quantity = postdata['quantity']
  cart_item = get_single_item(request, item_id)
  if cart_item:
    if int(quantity) > 0:
      cart_item.quantity = int(quantity)
      cart_item.save()
    else:
      remove_from_cart(request)


def remove_from_cart(request):
  """Remove a single item from cart
  """
  postdata = request.POST.copy()
  item_id = postdata['item_id']
  cart_item = get_single_item(request, item_id)
  if cart_item:
    cart_item.delete()


def cart_subtotal(request):
  """Gets the total cost for the current cart
  """
  cart_total = decimal.Decimal('0.00')
  cart_products = get_cart_items(request)
  for cart_item in cart_products:
    cart_total += cart_item.product.price * cart_item.quantity
  return cart_total
