# ZB Front Safe Release

`/var/www/zhilibyli/frontend_v2` — неизменяемая исходная точка. Новые сборки создаются только в `frontend_releases/releases`.

## Основные команды

Запускать от пользователя `zhilibyli`, без `sudo`:

```bash
cd /var/www/zhilibyli/frontend_releases

# Состояние, ссылки и процессы
make -s status

# Собрать новый release, проверить на 3010 и переключить production
make prod-deploy

# Вернуться на previous release
make rollback
```

## Логика prod-deploy

1. Получить точный commit ветки `master`.
2. Клонировать код в новый каталог `releases/<date>-<commit>`.
3. Подключить `shared/.env.local`.
4. Выполнить `sync-vendors`, `pnpm install` и production build.
5. Переключить `candidate` и проверить его на порту `3010`.
6. Сохранить старый `current` как `previous`.
7. Атомарно переключить `current`.
8. Перезапустить три процесса на `3000/3001/3002`.
9. Проверить три локальных health-check и публичный сайт.
10. При ошибке автоматически вернуть прежний `current`.

## Процессы

```text
zb_node_front_release_00 -> 127.0.0.1:3000
zb_node_front_release_01 -> 127.0.0.1:3001
zb_node_front_release_02 -> 127.0.0.1:3002
zb_node_front_candidate  -> 127.0.0.1:3010 (только на время проверки)
```

Все три production-процесса всегда запускаются из одного symlink `current` и используют один `.next/BUILD_ID`.

Пользователь `zhilibyli` не имеет общего беспарольного `sudo`: разрешён только защищённый helper для просмотра и перезапуска этих трёх процессов Supervisor.

## Telegram-уведомления

Используется legacy-формат уведомлений `ZB-FRONT`. Значения `BUILD_TELEGRAM_BOT_TOKEN` и `BUILD_TELEGRAM_CHAT_ID` читаются из `shared/.env.local`. Старт отправляется при `make release`, успех — после `make promote`, ошибка — при сбое сборки или публикации. Ошибка Telegram не останавливает deploy.
