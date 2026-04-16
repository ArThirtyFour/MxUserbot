Основные директории, на которые стоит смотреть при чтении кода:

- `src/mxuserbot/__main__.py` — запуск бота, web-auth, crypto, регистрация хендлеров.
- `src/mxuserbot/core/` — базовый framework: loader, utils, security, types, callbacks.
- `src/mxuserbot/modules/core/` — встроенные core-модули.
- `src/mxuserbot/modules/community/` — внешние и пользовательские модули.
- `src/database/` — простая прослойка над хранилищем настроек.