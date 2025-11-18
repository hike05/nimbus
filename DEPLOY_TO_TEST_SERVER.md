# Развертывание на тестовом сервере

## Предварительные требования

- Ubuntu/Debian сервер с минимум 1 CPU и 1 GB RAM
- Доменное имя, указывающее на IP сервера
- Порты 80 и 443 открыты
- SSH доступ к серверу

## Шаг 1: Подключение к серверу

```bash
ssh user@your-server-ip
```

## Шаг 2: Клонирование репозитория

```bash
# Установка git если не установлен
sudo apt update
sudo apt install -y git

# Клонирование репозитория
git clone https://github.com/hike05/nimbus.git
cd nimbus
```

## Шаг 3: Настройка переменных окружения

```bash
# Копирование примера конфигурации
cp .env.example .env

# Редактирование .env файла
nano .env
```

Обязательно укажите:
- `DOMAIN=your-domain.com` - ваш домен
- `EMAIL=your-email@example.com` - email для SSL сертификатов

## Шаг 4: Запуск установки

```bash
# Сделать скрипт исполняемым
chmod +x install.sh

# Запустить установку
sudo ./install.sh
```

Скрипт автоматически:
- Установит Docker и Docker Compose
- Определит ресурсы системы (CPU/RAM)
- Создаст необходимые директории
- Сгенерирует конфигурации для всех сервисов
- Создаст первого пользователя
- Запустит все контейнеры
- Получит SSL сертификаты
- Выполнит проверку здоровья всех сервисов

## Шаг 5: Проверка статуса

После установки проверьте статус сервисов:

```bash
docker compose ps
```

Все сервисы должны быть в статусе "Up":
- `gateway` - Caddy reverse proxy
- `proxy-a` - Xray-core
- `proxy-b` - Trojan-Go
- `proxy-c` - Sing-box
- `proxy-d` - WireGuard
- `web` - Admin panel

## Шаг 6: Доступ к админ-панели

1. Откройте браузер и перейдите на: `https://your-domain.com/admin/login`

2. Войдите используя учетные данные, которые были показаны в конце установки:
   - Username: `admin`
   - Password: (показан в выводе install.sh)

3. Первый пользователь прокси уже создан автоматически

## Проверка работоспособности

### Проверка сервисов

```bash
# Проверка всех сервисов
./scripts/health-check.sh

# Проверка логов
docker compose logs -f

# Проверка конкретного сервиса
docker compose logs -f proxy-a
```

### Проверка SSL сертификатов

```bash
# Проверка сертификата
curl -I https://your-domain.com

# Проверка Caddy
./scripts/caddy-health.sh
```

### Проверка админ-панели

1. Зайдите в админ-панель
2. Проверьте раздел "System Monitoring" - все сервисы должны быть "Running"
3. Проверьте раздел "Proxy Users" - должен быть создан первый пользователь
4. Скачайте конфигурации клиента для тестирования

## Тестирование клиентских подключений

### Xray (VLESS)

1. В админ-панели откройте конфигурации пользователя
2. Скопируйте "Xray XTLS-Vision" ссылку
3. Импортируйте в клиент v2rayNG (Android) или v2rayN (Windows)
4. Подключитесь и проверьте доступ к интернету

### Trojan

1. Скопируйте "Trojan" ссылку из админ-панели
2. Импортируйте в клиент Trojan
3. Подключитесь и проверьте

### WireGuard

1. Скачайте WireGuard конфигурацию (.conf файл)
2. Импортируйте в официальный клиент WireGuard
3. Подключитесь и проверьте

## Управление пользователями

### Создание нового пользователя

Через админ-панель:
1. Нажмите "Add New User"
2. Введите имя пользователя
3. Нажмите "Create User"
4. Конфигурации будут сгенерированы автоматически

Через командную строку:
```bash
docker compose exec web python3 /app/scripts/create-first-user.py username
```

### Удаление пользователя

Через админ-панель:
1. Найдите пользователя в списке
2. Нажмите кнопку удаления (корзина)
3. Подтвердите удаление

## Резервное копирование

### Создание бэкапа

Через админ-панель:
1. Нажмите "Create Backup"
2. Добавьте описание (опционально)
3. Нажмите "Create Backup"

Через командную строку:
```bash
# Создание бэкапа вручную
docker compose exec web python3 -c "
from core.backup_manager import BackupManager
bm = BackupManager('/data/proxy/configs')
print(bm.create_backup('Manual backup'))
"
```

### Восстановление из бэкапа

Через админ-панель:
1. Откройте "Manage Backups"
2. Найдите нужный бэкап
3. Нажмите "Restore"
4. Подтвердите восстановление

## Мониторинг

### Просмотр логов

В админ-панели:
1. Перейдите в раздел "Service Logs"
2. Выберите сервис
3. Выберите уровень логирования
4. Нажмите "Refresh"

Через командную строку:
```bash
# Все логи
docker compose logs -f

# Конкретный сервис
docker compose logs -f proxy-a

# Последние 100 строк
docker compose logs --tail=100 proxy-a
```

### Мониторинг ресурсов

В админ-панели раздел "System Monitoring" показывает:
- CPU usage
- Memory usage
- Disk usage
- Network I/O
- Статус каждого сервиса

## Обновление системы

### Обновление Docker образов

Через админ-панель:
1. Перейдите в "System Update"
2. Нажмите "Check for Updates"
3. Нажмите "Pull Latest Images"
4. Дождитесь завершения обновления

Через командную строку:
```bash
# Остановка сервисов
docker compose down

# Обновление образов
docker compose pull

# Запуск сервисов
docker compose up -d
```

## Устранение неполадок

### Сервис не запускается

```bash
# Проверка логов
docker compose logs service-name

# Перезапуск сервиса
docker compose restart service-name

# Пересоздание контейнера
docker compose up -d --force-recreate service-name
```

### SSL сертификат не получен

```bash
# Проверка логов Caddy
docker compose logs gateway

# Проверка DNS
dig your-domain.com

# Проверка портов
sudo netstat -tulpn | grep -E ':(80|443)'

# Перезапуск Caddy
docker compose restart gateway
```

### Админ-панель недоступна

```bash
# Проверка статуса
docker compose ps web

# Проверка логов
docker compose logs web

# Перезапуск
docker compose restart web
```

### Пользователь не может подключиться

1. Проверьте статус сервисов в админ-панели
2. Проверьте логи соответствующего сервиса
3. Убедитесь, что конфигурация клиента актуальна
4. Попробуйте другой протокол (Xray → Trojan → WireGuard)

## Полезные команды

```bash
# Статус всех сервисов
docker compose ps

# Остановка всех сервисов
docker compose down

# Запуск всех сервисов
docker compose up -d

# Перезапуск всех сервисов
docker compose restart

# Просмотр использования ресурсов
docker stats

# Очистка неиспользуемых образов
docker system prune -a

# Резервное копирование данных
sudo tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Восстановление данных
sudo tar -xzf backup-YYYYMMDD.tar.gz
```

## Безопасность

### Рекомендации

1. **Регулярно обновляйте систему:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Настройте firewall:**
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

3. **Регулярно создавайте бэкапы**

4. **Мониторьте логи на подозрительную активность**

5. **Используйте сильный пароль для админ-панели**

6. **Ограничьте SSH доступ:**
   ```bash
   # Отключите root login
   sudo nano /etc/ssh/sshd_config
   # PermitRootLogin no
   sudo systemctl restart sshd
   ```

## Поддержка

При возникновении проблем:
1. Проверьте логи сервисов
2. Проверьте статус в админ-панели
3. Запустите health-check.sh
4. Проверьте документацию в репозитории

## Следующие шаги

После успешного развертывания:
1. Создайте дополнительных пользователей
2. Настройте регулярные бэкапы
3. Настройте мониторинг
4. Протестируйте все протоколы подключения
5. Настройте автоматические обновления (опционально)
