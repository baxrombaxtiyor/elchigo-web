# ELCHIGO Web Panel — Django + Firebase

## 📁 Структура проекта
```
elchigo_web/
├── elchigo/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── views.py
│   ├── firebase.py
│   └── wsgi.py
├── templates/
│   ├── base.html
│   ├── auth/login.html
│   ├── dashboard/index.html
│   ├── orders/index.html
│   ├── menu/index.html
│   ├── tables/index.html + qr.html
│   ├── stats/index.html
│   └── settings/index.html
├── static/
├── manage.py
├── requirements.txt
└── serviceAccountKey.json  ← ДОБАВИТЬ СЮДА
```

## 🚀 Запуск

### 1. Установить зависимости
```bash
pip install -r requirements.txt
```

### 2. Добавить serviceAccountKey.json
Скопируйте скачанный файл в корень проекта (рядом с manage.py)

### 3. Добавить Firebase Web конфиг в login.html
Откройте templates/auth/login.html и замените:
```js
const firebaseConfig = {
  apiKey: "AIzaSyBpO6ExODPf-U2pnE-SQ7g99m-VT4BLYj4",
  authDomain: "elchi-2ffef.firebaseapp.com",
  projectId: "elchi-2ffef",
  storageBucket: "elchi-2ffef.firebasestorage.app",
  messagingSenderId: "796988718541",
  appId: "1:796988718541:web:402e5e42eaed050b521884",
  measurementId: "G-5QP3JRT9MT"
};
```

### 4. Создать .env файл (опционально)
```
SECRET_KEY=your-secret-key-here
FIREBASE_CREDENTIALS=serviceAccountKey.json
```

### 5. Запустить сервер
```bash
python manage.py runserver
```

Откройте: http://localhost:8000

## 🔥 Firebase Firestore — структура данных

```
users/
  {uid}/
    restaurantId: "..."
    isAdmin: true

restaurants/
  {restaurantId}/
    name: "..."
    isOpen: true
    schedule: [...]
    categories/
      {catId}/
        name: "..."
        dishes/
          {dishId}/
            name: "..."
            price: 25000
    tables/
      {tableId}/
        number: "1"
        seats: 4

orders/
  {orderId}/
    restaurantId: "..."
    name: "..."
    phone: "..."
    status: "pending"
    totalPrice: 50000
    items: [...]
    createdAt: timestamp
```

## 📋 Firestore Rules (добавить в Firebase Console)
```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```
