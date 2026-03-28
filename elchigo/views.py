# elchigo/views.py
import json
import logging
from datetime import datetime, timedelta
from functools import wraps

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .firebase import get_db, get_auth
from firebase_admin import auth as fb_auth
from firebase_admin import firestore
FieldValue = firestore.SERVER_TIMESTAMP

logger = logging.getLogger(__name__)


def login_required(f):
    @wraps(f)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('uid'):
            return redirect('login')
        return f(request, *args, **kwargs)
    return wrapper

def get_restaurant_id(request):
    return request.session.get('restaurant_id', '')

def _parse_dt(created):
    if created is None: return None
    try:
        if hasattr(created, 'ToDatetime'): return created.ToDatetime()
        if hasattr(created, 'timestamp') and hasattr(created, 'date'):
            return created.replace(tzinfo=None)
        if isinstance(created, str):
            s = created.replace('Z','').replace('+00:00','').strip()
            for fmt in ('%Y-%m-%dT%H:%M:%S.%f','%Y-%m-%dT%H:%M:%S','%Y-%m-%d'):
                try: return datetime.strptime(s[:26], fmt)
                except: continue
        return None
    except: return None


# ─── AUTH ─────────────────────────────────────────────────────────────────────

@csrf_exempt
def login_view(request):
    if request.session.get('uid'):
        return redirect('dashboard')
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            id_token = body.get('idToken')
        except Exception as e:
            logger.error(f"Login parse error: {e}")
            id_token = request.POST.get('idToken')

        if not id_token:
            return JsonResponse({'error': 'Token not provided'}, status=400)

        try:
            logger.info("Verifying Firebase token...")
            decoded = fb_auth.verify_id_token(id_token, check_revoked=False)
            uid = decoded['uid']
            logger.info(f"Token verified for uid: {uid}")

            db = get_db()
            user_doc = db.collection('users').document(uid).get()
            if not user_doc.exists:
                return JsonResponse({'error': 'Пользователь не найден'}, status=403)

            user_data = user_doc.to_dict()
            restaurant_id = user_data.get('restaurantId', '')
            request.session['uid'] = uid
            request.session['email'] = decoded.get('email', '')
            request.session['restaurant_id'] = restaurant_id

            if restaurant_id:
                rest_doc = db.collection('restaurants').document(restaurant_id).get()
                if rest_doc.exists:
                    request.session['restaurant_name'] = rest_doc.to_dict().get('name', '')

            logger.info("Login successful")
            return JsonResponse({'ok': True})

        except Exception as e:
            logger.error(f"Login error: {e}")
            return JsonResponse({'error': str(e)}, status=401)

    return render(request, 'auth/login.html')


def logout_view(request):
    request.session.flush()
    return redirect('login')


@csrf_exempt
def register_view(request):
    if request.session.get('uid'):
        return redirect('dashboard')
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            id_token        = body.get('idToken')
            restaurant_name = body.get('restaurantName', '').strip()
        except:
            id_token        = request.POST.get('idToken')
            restaurant_name = request.POST.get('restaurantName', '').strip()
        try:
            decoded = fb_auth.verify_id_token(id_token, check_revoked=False)
            uid = decoded['uid']; email = decoded.get('email', '')
            db = get_db()
            import uuid
            restaurant_id = 'rest_' + uuid.uuid4().hex[:8]
            db.collection('restaurants').document(restaurant_id).set({
                'name': restaurant_name, 'isOpen': True,
                'schedule': [{'enabled': i < 6, 'open': '09:00', 'close': '22:00'} for i in range(7)],
                'paymentMethods': [
                    {'id': 'Terminal', 'label': 'Terminal', 'icon': '💳', 'enabled': True},
                    {'id': 'Humo',     'label': 'Humo',     'icon': '🏦', 'enabled': True},
                    {'id': 'Click',    'label': 'Click',    'icon': '📱', 'enabled': True},
                    {'id': 'Payme',    'label': 'Payme',    'icon': '💜', 'enabled': True},
                    {'id': 'UZCARD',   'label': 'UZCARD',   'icon': '🟦', 'enabled': True},
                    {'id': 'Naqd',     'label': 'Naqd',     'icon': '💵', 'enabled': True},
                ],
            })
            db.collection('users').document(uid).set({
                'email': email, 'restaurantId': restaurant_id, 'isAdmin': True,
            })
            request.session['uid'] = uid
            request.session['email'] = email
            request.session['restaurant_id'] = restaurant_id
            request.session['restaurant_name'] = restaurant_name
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return render(request, 'auth/register.html')


# ─── DASHBOARD ────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    db  = get_db()
    rid = get_restaurant_id(request)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    orders_ref = db.collection('orders').where('restaurantId', '==', rid)
    all_orders = [o.to_dict() for o in orders_ref.stream()]
    total_orders  = len(all_orders)
    total_revenue = sum(o.get('totalPrice', 0) for o in all_orders if o.get('status') == 'delivered')
    active_orders = sum(1 for o in all_orders if o.get('status') not in ('delivered', 'cancelled'))
    cancelled     = sum(1 for o in all_orders if o.get('status') == 'cancelled')
    today_orders  = []
    for o in all_orders:
        dt = _parse_dt(o.get('createdAt'))
        if dt and (dt + timedelta(hours=5)).date() == today.date():
            today_orders.append(o)
    today_revenue = sum(o.get('totalPrice', 0) for o in today_orders if o.get('status') == 'delivered')
    recent = sorted(all_orders, key=lambda x: str(x.get('createdAt', '')), reverse=True)[:10]
    return render(request, 'dashboard/index.html', {
        'restaurant_name': request.session.get('restaurant_name', ''),
        'total_orders':    total_orders,
        'total_revenue':   f"{total_revenue:,.0f}".replace(',', ' '),
        'active_orders':   active_orders,
        'cancelled':       cancelled,
        'today_revenue':   f"{today_revenue:,.0f}".replace(',', ' '),
        'recent_orders':   recent,
    })


# ─── ORDERS ───────────────────────────────────────────────────────────────────

@login_required
def orders(request):
    return render(request, 'orders/index.html', {'restaurant_name': request.session.get('restaurant_name', '')})

@login_required
def orders_api(request):
    db  = get_db(); rid = get_restaurant_id(request); uid = request.session.get('uid', '')
    status_filter = request.GET.get('status', 'active')
    user_doc  = db.collection('users').document(uid).get()
    user_role = user_doc.to_dict().get('role', '') if user_doc.exists else ''
    result = []
    for doc in db.collection('orders').where('restaurantId', '==', rid).stream():
        o = doc.to_dict(); o['id'] = doc.id
        if user_role == 'waiter' and o.get('waiterId', '') != uid: continue
        dt = _parse_dt(o.get('createdAt'))
        o['createdAt'] = (dt + timedelta(hours=5)).strftime('%d.%m.%Y %H:%M') if dt else ''
        if status_filter == 'active':
            if o.get('status') not in ('delivered', 'cancelled'): result.append(o)
        else:
            if o.get('status') in ('delivered', 'cancelled'): result.append(o)
    result.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
    return JsonResponse({'orders': result})

@login_required
@csrf_exempt
def update_order_status(request, order_id):
    if request.method != 'POST': return JsonResponse({'error': 'Method not allowed'}, status=405)
    data = json.loads(request.body)
    get_db().collection('orders').document(order_id).update({'status': data.get('status')})
    return JsonResponse({'ok': True})


# ─── MENU ─────────────────────────────────────────────────────────────────────

@login_required
def menu(request):
    db  = get_db(); rid = get_restaurant_id(request); categories = []
    for cat in db.collection('restaurants').document(rid).collection('categories').order_by('order').stream():
        cat_data = cat.to_dict(); cat_data['id'] = cat.id; dishes = []
        for dish in db.collection('restaurants').document(rid).collection('categories').document(cat.id).collection('dishes').order_by('order').stream():
            d = dish.to_dict(); d['id'] = dish.id; dishes.append(d)
        cat_data['dishes'] = dishes; categories.append(cat_data)
    return render(request, 'menu/index.html', {'categories': categories, 'restaurant_name': request.session.get('restaurant_name', '')})

@login_required
@csrf_exempt
def add_category(request):
    if request.method != 'POST': return JsonResponse({'error': 'Method not allowed'}, status=405)
    data = json.loads(request.body); db = get_db(); rid = get_restaurant_id(request)
    col = db.collection('restaurants').document(rid).collection('categories')
    col.add({'name': data.get('name', ''), 'imageUrl': data.get('imageUrl', ''), 'order': len(list(col.stream()))})
    return JsonResponse({'ok': True})

@login_required
@csrf_exempt
def delete_category(request, cat_id):
    if request.method != 'DELETE': return JsonResponse({'error': 'Method not allowed'}, status=405)
    db = get_db(); rid = get_restaurant_id(request)
    for d in db.collection('restaurants').document(rid).collection('categories').document(cat_id).collection('dishes').stream():
        d.reference.delete()
    db.collection('restaurants').document(rid).collection('categories').document(cat_id).delete()
    return JsonResponse({'ok': True})

@login_required
@csrf_exempt
def add_dish(request, cat_id):
    if request.method != 'POST': return JsonResponse({'error': 'Method not allowed'}, status=405)
    data = json.loads(request.body); db = get_db(); rid = get_restaurant_id(request)
    col = db.collection('restaurants').document(rid).collection('categories').document(cat_id).collection('dishes')
    col.add({'name': data.get('name', ''), 'description': data.get('description', ''),
             'price': int(data.get('price', 0)), 'imageUrl': data.get('imageUrl', ''),
             'isAvailable': True, 'order': len(list(col.stream()))})
    return JsonResponse({'ok': True})

@login_required
@csrf_exempt
def delete_dish(request, cat_id, dish_id):
    if request.method != 'DELETE': return JsonResponse({'error': 'Method not allowed'}, status=405)
    db = get_db(); rid = get_restaurant_id(request)
    db.collection('restaurants').document(rid).collection('categories').document(cat_id).collection('dishes').document(dish_id).delete()
    return JsonResponse({'ok': True})

@login_required
@csrf_exempt
def update_dish_availability(request, cat_id, dish_id):
    if request.method != 'POST': return JsonResponse({'error': 'Method not allowed'}, status=405)
    data = json.loads(request.body); db = get_db(); rid = get_restaurant_id(request)
    db.collection('restaurants').document(rid).collection('categories').document(cat_id).collection('dishes').document(dish_id).update({'isAvailable': data.get('isAvailable', True)})
    return JsonResponse({'ok': True})

def customer_menu(request, restaurant_id, table_id):
    firebase_config = {'projectId': settings.FIREBASE_PROJECT_ID, 'apiKey': settings.FIREBASE_API_KEY}
    return render(request, 'menu/customer.html', {
        'restaurant_id': restaurant_id, 'table_id': table_id,
        'firebase_config_json': json.dumps(firebase_config),
    })


# ─── TABLES ───────────────────────────────────────────────────────────────────

@login_required
def tables(request):
    db = get_db(); rid = get_restaurant_id(request); tables_list = []
    for t in db.collection('restaurants').document(rid).collection('tables').stream():
        td = t.to_dict(); td['id'] = t.id; tables_list.append(td)
    waiters = []
    for doc in db.collection('users').where('restaurantId', '==', rid).stream():
        d = doc.to_dict()
        if d.get('role') == 'waiter':
            waiters.append({'uid': doc.id, 'name': d.get('name', d.get('email', ''))})
    return render(request, 'tables/index.html', {
        'tables': tables_list, 'restaurant_name': request.session.get('restaurant_name', ''),
        'restaurant_id': rid, 'waiters': waiters,
    })

@login_required
@csrf_exempt
def add_table(request):
    if request.method != 'POST': return JsonResponse({'error': 'Method not allowed'}, status=405)
    data = json.loads(request.body); db = get_db(); rid = get_restaurant_id(request)
    db.collection('restaurants').document(rid).collection('tables').add({
        'number': data.get('number', ''), 'seats': int(data.get('seats', 4)),
        'status': 'free', 'waiterId': data.get('waiterId', ''),
        'waiterName': data.get('waiterName', ''), 'category': data.get('category', ''),
    })
    return JsonResponse({'ok': True})

@login_required
@csrf_exempt
def assign_table_waiter(request, table_id):
    if request.method != 'POST': return JsonResponse({'error': 'Method not allowed'}, status=405)
    data = json.loads(request.body); db = get_db(); rid = get_restaurant_id(request)
    db.collection('restaurants').document(rid).collection('tables').document(table_id).update({
        'waiterId': data.get('waiterId', ''), 'waiterName': data.get('waiterName', ''),
    })
    return JsonResponse({'ok': True})

@login_required
@csrf_exempt
def delete_table(request, table_id):
    if request.method != 'DELETE': return JsonResponse({'error': 'Method not allowed'}, status=405)
    db = get_db(); rid = get_restaurant_id(request)
    db.collection('restaurants').document(rid).collection('tables').document(table_id).delete()
    return JsonResponse({'ok': True})

@login_required
def table_qr(request, table_id):
    rid = get_restaurant_id(request)
    qr_url = request.build_absolute_uri(f'/menu/{rid}/{table_id}/')
    return render(request, 'tables/qr.html', {
        'table_id': table_id, 'qr_url': qr_url,
        'restaurant_name': request.session.get('restaurant_name', ''),
    })

@login_required
@csrf_exempt
def table_categories(request):
    db = get_db(); rid = get_restaurant_id(request)
    if request.method == 'GET':
        doc = db.collection('restaurants').document(rid).get()
        data = doc.to_dict() if doc.exists else {}
        return JsonResponse({'categories': data.get('tableCategories', [])})
    if request.method == 'POST':
        data = json.loads(request.body); name = data.get('name', '').strip()
        if not name: return JsonResponse({'error': 'Название обязательно'}, status=400)
        doc = db.collection('restaurants').document(rid).get()
        rest = doc.to_dict() if doc.exists else {}
        cats = rest.get('tableCategories', [])
        if name not in cats: cats.append(name)
        db.collection('restaurants').document(rid).update({'tableCategories': cats})
        return JsonResponse({'ok': True})
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
@csrf_exempt
def table_category_delete(request):
    if request.method != 'POST': return JsonResponse({'error': 'Method not allowed'}, status=405)
    data = json.loads(request.body); name = data.get('name', '')
    db = get_db(); rid = get_restaurant_id(request)
    doc = db.collection('restaurants').document(rid).get()
    rest = doc.to_dict() if doc.exists else {}
    cats = [c for c in rest.get('tableCategories', []) if c != name]
    db.collection('restaurants').document(rid).update({'tableCategories': cats})
    for t in db.collection('restaurants').document(rid).collection('tables').stream():
        if t.to_dict().get('category') == name:
            t.reference.update({'category': ''})
    return JsonResponse({'ok': True})

@login_required
@csrf_exempt
def update_table_category(request, table_id):
    if request.method != 'POST': return JsonResponse({'error': 'Method not allowed'}, status=405)
    data = json.loads(request.body); db = get_db(); rid = get_restaurant_id(request)
    db.collection('restaurants').document(rid).collection('tables').document(table_id).update({'category': data.get('category', '')})
    return JsonResponse({'ok': True})


# ─── STATS ────────────────────────────────────────────────────────────────────

@login_required
def stats(request):
    return render(request, 'stats/index.html', {'restaurant_name': request.session.get('restaurant_name', '')})

@login_required
def stats_api(request):
    db = get_db(); rid = get_restaurant_id(request)
    period = request.GET.get('period', 'week')
    now = datetime.now()
    if period == 'today': start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'month': start = now - timedelta(days=30)
    else: start = now - timedelta(days=7)
    daily = {}; dish_count = {}; total_revenue = 0
    delivered_orders = list(db.collection('orders').where('restaurantId', '==', rid).where('status', '==', 'delivered').stream())
    for doc in delivered_orders:
        o = doc.to_dict()
        dt = _parse_dt(o.get('createdAt'))
        if not dt: continue
        dt_local = dt + timedelta(hours=5)
        if dt_local < start: continue
        day_key = dt_local.strftime('%d.%m')
        price = o.get('totalPrice', 0)
        daily[day_key] = daily.get(day_key, 0) + price
        total_revenue += price
        for item in o.get('items', []):
            name = item.get('dishName', ''); qty = item.get('quantity', 1)
            dish_count[name] = dish_count.get(name, 0) + qty
    top_dishes = sorted(dish_count.items(), key=lambda x: x[1], reverse=True)[:5]
    waiter_stats = {}
    for doc in delivered_orders:
        o = doc.to_dict()
        dt = _parse_dt(o.get('createdAt'))
        if not dt or (dt + timedelta(hours=5)) < start: continue
        wid = o.get('waiterId', ''); wname = o.get('waiterName', '') or wid
        if not wid: continue
        if wid not in waiter_stats:
            waiter_stats[wid] = {'name': wname, 'revenue': 0, 'orders': 0}
        waiter_stats[wid]['revenue'] += o.get('totalPrice', 0)
        waiter_stats[wid]['orders']  += 1
    waiters_list = sorted(waiter_stats.values(), key=lambda x: x['revenue'], reverse=True)[:8]
    cat_revenue = {}
    for doc in delivered_orders:
        o = doc.to_dict()
        dt = _parse_dt(o.get('createdAt'))
        if not dt or (dt + timedelta(hours=5)) < start: continue
        for item in o.get('items', []):
            cat = item.get('catName', 'Другое') or 'Другое'
            cat_revenue[cat] = cat_revenue.get(cat, 0) + float(item.get('total', 0))
    cats_list = sorted(cat_revenue.items(), key=lambda x: x[1], reverse=True)[:8]
    dish_images = {}
    for cat_doc in db.collection('restaurants').document(rid).collection('categories').stream():
        for dish_doc in db.collection('restaurants').document(rid).collection('categories').document(cat_doc.id).collection('dishes').stream():
            d = dish_doc.to_dict()
            dish_images[d.get('name', '')] = d.get('imageUrl', '')
    top_dishes_data = [{'name': k, 'count': v, 'image': dish_images.get(k, '')} for k, v in top_dishes]
    return JsonResponse({
        'daily': daily, 'top_dishes': top_dishes_data, 'total_revenue': total_revenue,
        'waiters': waiters_list, 'categories': [{'name': k, 'revenue': v} for k, v in cats_list],
    })


# ─── REPORTS ──────────────────────────────────────────────────────────────────

@login_required
def reports(request):
    return render(request, 'reports/index.html', {'restaurant_name': request.session.get('restaurant_name', '')})

@login_required
def reports_api(request):
    db = get_db(); rid = get_restaurant_id(request)
    period = request.GET.get('period', 'week')
    date_from = request.GET.get('from', ''); date_to = request.GET.get('to', '')
    now = datetime.now()
    if period == 'today': start = now.replace(hour=0, minute=0, second=0, microsecond=0); end = now
    elif period == 'week': start = now - timedelta(days=7); end = now
    elif period == 'month': start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0); end = now
    elif period == 'custom' and date_from and date_to:
        try:
            start = datetime.strptime(date_from, '%Y-%m-%d')
            end   = datetime.strptime(date_to, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        except: start = now - timedelta(days=7); end = now
    else: start = now - timedelta(days=7); end = now
    all_orders = []
    for doc in db.collection('orders').where('restaurantId', '==', rid).stream():
        o = doc.to_dict(); o['id'] = doc.id
        dt = _parse_dt(o.get('createdAt'))
        if dt and start <= dt <= end:
            o['_dt'] = dt; all_orders.append(o)
    delivered = [o for o in all_orders if o.get('status') == 'delivered']
    cancelled = [o for o in all_orders if o.get('status') == 'cancelled']
    active    = [o for o in all_orders if o.get('status') != 'cancelled']
    daily = {}
    for o in active:
        day = o['_dt'].strftime('%d.%m'); daily[day] = daily.get(day, 0) + o.get('totalPrice', 0)
    dish_count = {}; dish_revenue = {}
    for o in active:
        for item in o.get('items', []):
            name = item.get('dishName', '') or item.get('name', '')
            qty = int(item.get('quantity', 1)); price = float(item.get('price', 0))
            dish_count[name] = dish_count.get(name, 0) + qty
            dish_revenue[name] = dish_revenue.get(name, 0) + price * qty
    top_dishes = sorted(dish_count.items(), key=lambda x: x[1], reverse=True)[:10]
    waiter_stats = {}
    for o in all_orders:
        wid = o.get('waiterId', ''); wname = o.get('waiterName', '') or wid
        if not wid: continue
        if wid not in waiter_stats:
            waiter_stats[wid] = {'name': wname, 'orders': 0, 'delivered': 0, 'cancelled': 0, 'revenue': 0}
        waiter_stats[wid]['orders'] += 1
        if o.get('status') != 'cancelled': waiter_stats[wid]['revenue'] += o.get('totalPrice', 0)
        if o.get('status') == 'delivered': waiter_stats[wid]['delivered'] += 1
        elif o.get('status') == 'cancelled': waiter_stats[wid]['cancelled'] += 1
    waiters_list = sorted(waiter_stats.values(), key=lambda x: x['revenue'], reverse=True)
    table_stats = {}
    for o in active:
        tnum = str(o.get('tableNumber', ''))
        if not tnum: continue
        if tnum not in table_stats: table_stats[tnum] = {'orders': 0, 'revenue': 0}
        table_stats[tnum]['orders'] += 1; table_stats[tnum]['revenue'] += o.get('totalPrice', 0)
    tables_list = [{'table': k, 'orders': v['orders'], 'revenue': v['revenue']}
                   for k, v in sorted(table_stats.items(), key=lambda x: x[1]['revenue'], reverse=True)]
    total_revenue = sum(o.get('totalPrice', 0) for o in active)
    avg_order = total_revenue / len(active) if active else 0
    return JsonResponse({
        'summary': {'total_orders': len(all_orders), 'delivered': len(delivered),
                    'cancelled': len(cancelled), 'total_revenue': total_revenue, 'avg_order': avg_order},
        'daily': daily,
        'top_dishes': [{'name': k, 'count': v, 'revenue': dish_revenue.get(k, 0)} for k, v in top_dishes],
        'waiters': waiters_list, 'tables': tables_list[:10],
    })

@login_required
def waiter_report(request):
    return render(request, 'reports/waiter_report.html', {'restaurant_name': request.session.get('restaurant_name', '')})

@login_required
def z_report(request):
    return render(request, 'reports/z_report.html', {'restaurant_name': request.session.get('restaurant_name', '')})

@login_required
@csrf_exempt
def z_report_close(request):
    if request.method != 'POST': return JsonResponse({'error': 'Method not allowed'}, status=405)
    data = json.loads(request.body); db = get_db(); rid = get_restaurant_id(request)
    db.collection('z_reports').add({
        'restaurantId': rid, 'date': data.get('date', ''),
        'revenue': data.get('revenue', 0), 'orders': data.get('orders', 0),
        'closedBy': request.session.get('uid', ''), 'closedAt': firestore.SERVER_TIMESTAMP,
    })
    return JsonResponse({'ok': True})


# ─── SETTINGS ─────────────────────────────────────────────────────────────────

@login_required
def restaurant_settings(request):
    db = get_db(); rid = get_restaurant_id(request)
    rest_doc = db.collection('restaurants').document(rid).get()
    rest_data = rest_doc.to_dict() if rest_doc.exists else {}
    if request.method == 'POST':
        data = json.loads(request.body)
        db.collection('restaurants').document(rid).update({
            'name': data.get('name', ''), 'isOpen': data.get('isOpen', True),
            'schedule': data.get('schedule', []),
        })
        request.session['restaurant_name'] = data.get('name', '')
        return JsonResponse({'ok': True})
    return render(request, 'settings/index.html', {
        'restaurant': rest_data, 'restaurant_name': request.session.get('restaurant_name', ''),
    })

@login_required
def payment_methods_api(request):
    db = get_db(); rid = get_restaurant_id(request)
    if request.method == 'GET':
        rest_doc = db.collection('restaurants').document(rid).get()
        if not rest_doc.exists: return JsonResponse({'methods': []})
        methods = rest_doc.to_dict().get('paymentMethods', [])
        return JsonResponse({'methods': methods})
    if request.method == 'POST':
        data = json.loads(request.body)
        db.collection('restaurants').document(rid).update({'paymentMethods': data.get('methods', [])})
        return JsonResponse({'ok': True})
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ─── STAFF ────────────────────────────────────────────────────────────────────

@login_required
def staff(request):
    return render(request, 'staff/index.html', {
        'restaurant_name': request.session.get('restaurant_name', ''),
        'restaurant_id':   request.session.get('restaurant_id', ''),
    })

@login_required
def staff_api(request):
    db = get_db(); rid = get_restaurant_id(request); users = []
    for doc in db.collection('users').where('restaurantId', '==', rid).stream():
        d = doc.to_dict(); role = d.get('role', '')
        if role not in ('waiter', 'manager', 'cook', 'cashier'): continue
        users.append({'uid': doc.id, 'name': d.get('name', ''), 'email': d.get('email', ''),
                      'phone': d.get('phone', ''), 'role': role, 'restaurantId': rid,
                      'restaurantName': '', 'blocked': d.get('blocked', False)})
    users.sort(key=lambda x: (x['name'] or x['email']).lower())
    return JsonResponse({'staff': users})

@login_required
@csrf_exempt
def staff_create(request):
    if request.method != 'POST': return JsonResponse({'error': 'Method not allowed'}, status=405)
    data = json.loads(request.body)
    first_name = data.get('firstName', '').strip(); last_name = data.get('lastName', '').strip()
    email = data.get('email', '').strip(); password = data.get('password', '').strip()
    phone = data.get('phone', '').strip(); role = data.get('role', 'waiter').strip()
    rid = get_restaurant_id(request)
    if not first_name or not email or not password:
        return JsonResponse({'error': 'Имя, email и пароль обязательны'}, status=400)
    if len(password) < 6:
        return JsonResponse({'error': 'Пароль минимум 6 символов'}, status=400)
    try:
        user = fb_auth.create_user(email=email, password=password,
                                   display_name=f'{first_name} {last_name}'.strip())
        db = get_db()
        db.collection('users').document(user.uid).set({
            'firstName': first_name, 'lastName': last_name,
            'name': f'{first_name} {last_name}'.strip(),
            'email': email, 'phone': phone, 'role': role, 'restaurantId': rid, 'blocked': False,
        })
        return JsonResponse({'ok': True, 'uid': user.uid})
    except Exception as e:
        err = str(e)
        if 'EMAIL_EXISTS' in err or 'email-already-exists' in err:
            return JsonResponse({'error': 'Этот email уже используется'}, status=400)
        return JsonResponse({'error': err}, status=400)

@login_required
@csrf_exempt
def staff_update(request, uid):
    if request.method != 'POST': return JsonResponse({'error': 'Method not allowed'}, status=405)
    data = json.loads(request.body); db = get_db()
    update_data = {f: data[f] for f in ('name', 'phone', 'role', 'restaurantId') if f in data}
    db.collection('users').document(uid).update(update_data)
    return JsonResponse({'ok': True})

@login_required
@csrf_exempt
def staff_block(request, uid):
    if request.method != 'POST': return JsonResponse({'error': 'Method not allowed'}, status=405)
    if uid == request.session.get('uid'):
        return JsonResponse({'error': 'Нельзя заблокировать свой аккаунт'}, status=400)
    data = json.loads(request.body); blocked = bool(data.get('blocked', False))
    db = get_db()
    db.collection('users').document(uid).update({'blocked': blocked})
    try: fb_auth.update_user(uid, disabled=blocked)
    except Exception as e: return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'ok': True})

@login_required
@csrf_exempt
def staff_delete(request, uid):
    if request.method != 'DELETE': return JsonResponse({'error': 'Method not allowed'}, status=405)
    db = get_db()
    db.collection('users').document(uid).delete()
    try: fb_auth.delete_user(uid)
    except: pass
    return JsonResponse({'ok': True})


# ─── FINANCE ──────────────────────────────────────────────────────────────────

@login_required
def finance(request):
    return render(request, 'finance/index.html', {'restaurant_name': request.session.get('restaurant_name', '')})

@login_required
def finance_api(request):
    db = get_db(); rid = get_restaurant_id(request)
    period = request.GET.get('period', 'today'); now = datetime.now()
    date_from = request.GET.get('from', ''); date_to = request.GET.get('to', '')
    if period == 'today': start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week': start = now - timedelta(days=7)
    elif period == 'month': start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == 'custom' and date_from and date_to:
        try: start = datetime.strptime(date_from, '%Y-%m-%d')
        except: start = datetime(2000, 1, 1)
    else: start = datetime(2000, 1, 1)
    transactions = []; daily = {}
    for doc in db.collection('payments').where('restaurantId', '==', rid).stream():
        p = doc.to_dict(); dt = _parse_dt(p.get('createdAt'))
        if not dt or dt < start: continue
        dt_local = dt + timedelta(hours=5); day = dt_local.strftime('%d.%m'); amount = p.get('total', 0)
        transactions.append({'id': doc.id, 'type': 'payment',
            'description': f"Стол {p.get('tableNumber', '?')}", 'category': 'Выручка',
            'method': p.get('paymentMethod', ''), 'amount': amount, 'date': dt_local.strftime('%d.%m.%Y %H:%M')})
        if day not in daily: daily[day] = {'income': 0, 'expense': 0}
        daily[day]['income'] += amount
    for doc in db.collection('expenses').where('restaurantId', '==', rid).stream():
        e = doc.to_dict(); dt = _parse_dt(e.get('createdAt'))
        if not dt or dt < start: continue
        dt_local = dt + timedelta(hours=5); day = dt_local.strftime('%d.%m'); amount = e.get('amount', 0)
        transactions.append({'id': doc.id, 'type': 'expense',
            'description': e.get('description', ''), 'category': e.get('category', ''),
            'method': '—', 'amount': amount, 'date': dt_local.strftime('%d.%m.%Y %H:%M')})
        if day not in daily: daily[day] = {'income': 0, 'expense': 0}
        daily[day]['expense'] += amount
    transactions.sort(key=lambda x: x['date'], reverse=True)
    total_income  = sum(t['amount'] for t in transactions if t['type'] == 'payment')
    total_expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
    return JsonResponse({
        'transactions': transactions, 'total_income': total_income, 'total_expense': total_expense,
        'income_count': sum(1 for t in transactions if t['type'] == 'payment'),
        'expense_count': sum(1 for t in transactions if t['type'] == 'expense'),
        'daily': daily,
    })

@login_required
@csrf_exempt
def finance_expenses(request):
    db = get_db(); rid = get_restaurant_id(request)
    if request.method == 'GET':
        expenses = []
        for doc in db.collection('expenses').where('restaurantId', '==', rid).stream():
            e = doc.to_dict(); dt = _parse_dt(e.get('createdAt'))
            dt_local = (dt + timedelta(hours=5)).strftime('%d.%m.%Y') if dt else ''
            expenses.append({'id': doc.id, 'description': e.get('description', ''),
                'amount': e.get('amount', 0), 'category': e.get('category', ''),
                'date': dt_local, 'comment': e.get('comment', '')})
        return JsonResponse({'expenses': expenses})
    if request.method == 'POST':
        data = json.loads(request.body)
        desc = data.get('description', '').strip(); amount = float(data.get('amount', 0))
        if not desc or amount <= 0: return JsonResponse({'error': 'Описание и сумма обязательны'}, status=400)
        db.collection('expenses').add({'restaurantId': rid, 'description': desc, 'amount': amount,
            'category': data.get('category', ''), 'comment': data.get('comment', ''),
            'createdAt': firestore.SERVER_TIMESTAMP})
        return JsonResponse({'ok': True})
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
@csrf_exempt
def finance_expense_delete(request, expense_id):
    if request.method != 'DELETE': return JsonResponse({'error': 'Method not allowed'}, status=405)
    get_db().collection('expenses').document(expense_id).delete()
    return JsonResponse({'ok': True})

@login_required
def finance_categories(request):
    db = get_db(); rid = get_restaurant_id(request)
    if request.method == 'GET':
        doc = db.collection('restaurants').document(rid).get()
        data = doc.to_dict() if doc.exists else {}
        return JsonResponse({
            'expense': data.get('expenseCategories', ['Продукты', 'Аренда', 'Зарплата', 'Коммунальные', 'Прочее']),
            'income':  data.get('incomeCategories',  ['Выручка', 'Доставка', 'Банкет']),
        })
    if request.method == 'POST':
        data = json.loads(request.body); ctype = data.get('type'); name = data.get('name', '').strip()
        if not name: return JsonResponse({'error': 'Название обязательно'}, status=400)
        doc = db.collection('restaurants').document(rid).get()
        rest = doc.to_dict() if doc.exists else {}
        field = 'expenseCategories' if ctype == 'expense' else 'incomeCategories'
        cats = rest.get(field, [])
        if name not in cats: cats.append(name)
        db.collection('restaurants').document(rid).update({field: cats})
        return JsonResponse({'ok': True})
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
@csrf_exempt
def finance_category_delete(request):
    if request.method != 'POST': return JsonResponse({'error': 'Method not allowed'}, status=405)
    data = json.loads(request.body); ctype = data.get('type'); name = data.get('name', '')
    db = get_db(); rid = get_restaurant_id(request)
    doc = db.collection('restaurants').document(rid).get()
    rest = doc.to_dict() if doc.exists else {}
    field = 'expenseCategories' if ctype == 'expense' else 'incomeCategories'
    cats = [c for c in rest.get(field, []) if c != name]
    db.collection('restaurants').document(rid).update({field: cats})
    return JsonResponse({'ok': True})