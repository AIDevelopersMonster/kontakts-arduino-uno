# Публикация первой версии на GitHub

Рекомендуемое имя репозитория: `kontakts-arduino-uno`.

## Через веб-интерфейс

1. Создать пустой репозиторий без автоматически сгенерированных README и лицензии.
2. Распаковать архив `kontakts-arduino-uno-v0.1.0.zip`.
3. Загрузить содержимое каталога `kontakts-arduino-uno` в новый репозиторий.
4. Убедиться, что GitHub Actions запустил три job: `validate`, `arduino-cli`, `platformio`.
5. Включить Issues и Discussions, если они нужны.
6. В описании репозитория указать форум: `http://kontakts.ru/forumdisplay.php/191`.

## Через Git

```bash
cd kontakts-arduino-uno
git init -b main
git add .
git commit -m "Initial KONTAKTS Arduino UNO repository"
git remote add origin https://github.com/OWNER/kontakts-arduino-uno.git
git push -u origin main
```

`OWNER` заменяется именем пользователя или организации GitHub. Репозиторий намеренно не содержит выбранной свободной лицензии: это решение следует принять до первого публичного релиза.

## После публикации

- заменить пустые GitHub URL в `content/catalog.json`;
- добавить точный URL репозитория в `CITATION.cff`;
- создать milestone `v0.2 — UNO foundations`;
- превратить первые 12 публикаций из `docs/launch/first-12-publications.md` в issues;
- после первого стабильного релиза подключить репозиторий к Zenodo.
