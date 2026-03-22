# 🛒 Marketplace App

Учебный проект для курса Advanced Quality Assurance. Полноценный маркетплейс на Django REST Framework + React.

## Быстрый старт

### Требования
- Docker Desktop (запущен)
- Git

### Запуск
```bash
git clone <repo>
cd marketplace
docker-compose up --build
```

Первый запуск: ~3-5 минут.

## Доступ

| Сервис          | URL                          |
|-----------------|------------------------------|
| Frontend        | http://localhost:3000        |
| Backend API     | http://localhost:8000/api/   |
| Django Admin    | http://localhost:8000/admin/ |
| API Browsable   | http://localhost:8000/api/   |

## Тестовые аккаунты

| Роль     | Email                  | Password  |
|----------|------------------------|-----------|
| Admin    | admin@marketplace.com  | Admin123! |
| Seller   | seller1@test.com       | Test123!  |
| Buyer    | buyer1@test.com        | Test123!  |

## Купоны для тестирования

| Код      | Скидка |
|----------|--------|
| SAVE10   | 10%    |
| SAVE25   | 25%    |
| HALFOFF  | 50%    |

## Стек
- Backend: Python 3.11, Django 4.2, DRF, JWT
- Frontend: React 18, Vite, Tailwind CSS
- Database: SQLite
- Deploy: Docker Compose
