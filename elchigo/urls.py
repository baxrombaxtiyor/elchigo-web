from django.urls import path
from . import views

urlpatterns = [
    path('',            views.login_view,    name='login'),
    path('logout/',     views.logout_view,   name='logout'),
    path('register/',   views.register_view, name='register'),
    path('dashboard/',  views.dashboard,     name='dashboard'),

    path('orders/',     views.orders,        name='orders'),
    path('orders/api/', views.orders_api,    name='orders_api'),
    path('orders/<str:order_id>/status/', views.update_order_status, name='update_order_status'),

    path('menu/',                                        views.menu,            name='menu'),
    path('menu/category/add/',                           views.add_category,    name='add_category'),
    path('menu/category/<str:cat_id>/delete/',           views.delete_category, name='delete_category'),
    path('menu/category/<str:cat_id>/dish/add/',         views.add_dish,        name='add_dish'),
    path('menu/dish/<str:cat_id>/<str:dish_id>/delete/', views.delete_dish,     name='delete_dish'),
    path('menu/dish/<str:cat_id>/<str:dish_id>/availability/', views.update_dish_availability, name='update_dish_availability'),
    path('menu/<str:restaurant_id>/<str:table_id>/',     views.customer_menu,   name='customer_menu'),

    # Tables — статичные маршруты ПЕРЕД динамическими
    path('tables/',                          views.tables,                name='tables'),
    path('tables/add/',                      views.add_table,             name='add_table'),
    path('tables/categories/',               views.table_categories,      name='table_categories'),
    path('tables/categories/delete/',        views.table_category_delete, name='table_category_delete'),
    path('tables/<str:table_id>/delete/',    views.delete_table,          name='delete_table'),
    path('tables/<str:table_id>/qr/',        views.table_qr,              name='table_qr'),
    path('tables/<str:table_id>/assign/',    views.assign_table_waiter,   name='assign_table_waiter'),
    path('tables/<str:table_id>/category/',  views.update_table_category, name='update_table_category'),

    path('stats/',     views.stats,      name='stats'),
    path('stats/api/', views.stats_api,  name='stats_api'),

    path('reports/',         views.reports,       name='reports'),
    path('reports/api/',     views.reports_api,   name='reports_api'),
    path('reports/waiters/', views.waiter_report, name='waiter_report'),
    path('reports/z/',       views.z_report,      name='z_report'),
    path('reports/z-close/', views.z_report_close,name='z_report_close'),

    path('settings/',          views.restaurant_settings, name='settings'),
    path('settings/payments/', views.payment_methods_api, name='payment_methods_api'),

    path('staff/',                  views.staff,        name='staff'),
    path('staff/api/',              views.staff_api,    name='staff_api'),
    path('staff/create/',           views.staff_create, name='staff_create'),
    path('staff/<str:uid>/update/', views.staff_update, name='staff_update'),
    path('staff/<str:uid>/block/',  views.staff_block,  name='staff_block'),
    path('staff/<str:uid>/delete/', views.staff_delete, name='staff_delete'),

    # Finance
    path('finance/',                                  views.finance,                name='finance'),
    path('finance/api/',                              views.finance_api,            name='finance_api'),
    path('finance/expenses/',                         views.finance_expenses,       name='finance_expenses'),
    path('finance/expenses/<str:expense_id>/delete/', views.finance_expense_delete, name='finance_expense_delete'),
    path('finance/categories/',                       views.finance_categories,     name='finance_categories'),
    path('finance/categories/delete/',                views.finance_category_delete,name='finance_category_delete'),

    # Printers — статичные ПЕРЕД динамическими
    path('printers/',                             views.printers,             name='printers'),
    path('printers/api/',                         views.printers_api,         name='printers_api'),
    path('printers/add/',                         views.printer_add,          name='printer_add'),
    path('printers/receipt/',                     views.receipt_settings_view,name='receipt_settings'),
    path('printers/receipt-settings/',            views.receipt_settings_api, name='receipt_settings_api'),
    path('printers/receipt-settings/save/',       views.receipt_settings_api, name='receipt_settings_save'),
    path('printers/<str:printer_id>/update/',     views.printer_update,       name='printer_update'),
    path('printers/<str:printer_id>/delete/',     views.printer_delete,       name='printer_delete'),
    path('printers/<str:printer_id>/test/',       views.printer_test,         name='printer_test'),
]