import asyncio
import logging
import os
import pickle
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.environ.get('BOT_TOKEN')


class Dialog(StatesGroup):
    choose_domain_name = State()
    waiting_for_login = State()
    waiting_for_pass = State()
    waiting_for_confirmation = State()
    waiting_for_choice = State()
    waiting_for_delete_choice = State()
    delete_confirmation = State()


if __name__ == '__main__':
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    if os.stat("passw").st_size != 0:
        f = open("passw", 'rb')
        passwords = pickle.load(f)
        f.close()
    else:
        passwords = []


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! \nЯ умею хранить твои пароли. Напиши /set, чтобы создать первую запись")


@dp.message(Command("set"))
async def cmd_reply(message: types.Message, state: FSMContext):
    await message.reply("Давай создадим запись. Придумай название для этого пароля (например, название сервиса) или напиши /cancel, чтобы вернуться в начало")
    await state.set_state(Dialog.choose_domain_name)


@dp.message(Command("cancel"))
async def cancellation(message: types.Message, state: FSMContext):
    await message.answer(
        "Отменяю действие. Ты можешь написать /set, чтобы создать новую запись, /get, чтобы просмотреть список паролей, или /delete, чтобы удалить запись")
    await state.clear()


@dp.message(Dialog.choose_domain_name)
async def get_name(message: types.Message, state: FSMContext):
    presence = 0
    for i in passwords:
        if i[0] == message.from_user.id and i[1] == message.text.lower:
            presence = 1
    if presence == 1:
        await message.reply("Прости, ты уже использовал это название. Придумай другое, чтобы избежать путаницы")
    else:
        await state.update_data({'id': message.from_user.id, 'domain': message.text})
        await message.answer("\nХорошо, теперь напиши логин")
        await state.set_state(Dialog.waiting_for_login)


@dp.message(Dialog.waiting_for_login)
async def check_name(message: types.Message, state: FSMContext):
    passw = await state.get_data()
    passw['login'] = message.text
    await state.update_data(passw)
    await message.answer("Отлично, теперь напиши пароль для этого сервиса")
    await state.set_state(Dialog.waiting_for_pass)


@dp.message(Dialog.waiting_for_pass)
async def check_name(message: types.Message, state: FSMContext):
    passw = await state.get_data()
    passw['password'] = message.text
    await state.update_data(passw)
    newmsg = await message.answer(f"Отлично, вот твоя запись:\n\n{passw['domain']}\n{passw['login']}\n{passw['password']}\n\nНапиши Да, если все верно, или Нет, если хочешь изменить запись")
    await state.set_state(Dialog.waiting_for_confirmation)
    await asyncio.sleep(60)
    await message.delete()
    await newmsg.edit_text("_Я спрятал пароль в целях безопасности_\nТы можешь найти его, написав /get", parse_mode="markdown")



@dp.message(Dialog.waiting_for_confirmation)
async def is_alright(message: types.Message, state: FSMContext):
    passw = await state.get_data()
    if message.text.lower() == "да":
        passwords.append([passw['id'], passw['domain'], passw['login'], passw['password']])
        f = open("passw", 'wb')
        pickle.dump(passwords, f)
        f.close()
        await state.clear()
        await message.answer("Отлично! Теперь ты можешь написать /get, чтобы посмотреть свои пароли, или /delete, чтобы удалить ненужные")
    elif message.text.lower == "нет":
        await message.answer("Хорошо, давай попробуем еще раз. Как назовем запись?")
        await state.set_state(Dialog.choose_domain_name)
    else:
        await message.answer("Пожалуйста, ответь Да или Нет. Если передумал, напиши /cancel, чтобы вернуться в начало")


@dp.message(Command("get"))
async def reading(message: types, state: FSMContext):
    outp = []
    for i in passwords:
        if i[0] == message.from_user.id:
            outp.append(i[1])
    await message.answer("Вот список твоих паролей:\n"+"\n".join(outp)+"\n\nНапиши, какую запись ты хочешь просмотреть. \nПиши в точности так, как указано в списке")
    await state.set_state(Dialog.waiting_for_choice)


@dp.message(Dialog.waiting_for_choice)
async def output(message: types.Message, state: FSMContext):
    flag = 0
    for i in passwords:
        if i[1] == message.text:
            newmsg = await message.answer(f"Вот твоя запись:\nЛогин: <code>{i[2]}</code>\nПароль: <code>{i[3]}</code>", parse_mode="HTML")
            await state.clear()
            flag = 1
            await asyncio.sleep(60)
            await message.delete()
            await newmsg.edit_text("_Я спрятал пароль в целях безопасности_\nТы можешь найти его, написав /get",
                                   parse_mode="markdown")
    if flag != 1:
        await message.answer("Кажется, такой записи нет. Попробуй еще раз или напиши /cancel, чтобы вернуться в начало")


@dp.message(Command("delete"))
async def output(message: types.Message, state: FSMContext):
    outp = []
    for i in passwords:
        if i[0] == message.from_user.id:
            outp.append(i[1])
    await message.answer("Вот список твоих паролей:\n\n" + "\n".join(outp) + "\n\nНапиши, какую запись ты хочешь удалить. \nПиши в точности так, как указано в списке")
    await state.set_state(Dialog.waiting_for_delete_choice)


@dp.message(Dialog.waiting_for_delete_choice)
async def output(message: types.Message, state: FSMContext):
    flag = 0
    for i in passwords:
        if i[1] == message.text:
            passwords.remove(i)
            await message.answer("Готово")
            f = open("passw", 'wb')
            pickle.dump(passwords, f)
            f.close()
            await state.clear()
            flag = 1
    if flag != 1:
        await message.answer("Кажется, такой записи нет. Попробуй еще раз или напиши /cancel, чтобы вернуться в начало")


@dp.message(Dialog.delete_confirmation)
async def is_alright(message: types.Message, state: FSMContext):
    passw = await state.get_data()
    if message.text.lower() == "да":
        passwords.append([passw['id'], passw['domain'], passw['login'], passw['password']])
        f = open("passw", 'wb')
        pickle.dump(passwords, f)
        f.close()
        await state.clear()
        await message.answer("Отлично! Теперь ты можешь написать /get, чтобы посмотреть свои пароли")
    elif message.text.lower == "нет":
        await message.answer("Хорошо, давай попробуем еще раз. Как назовем запись?")
        await state.set_state(Dialog.choose_domain_name)
    else:
        await message.answer("Пожалуйста, ответь Да или Нет. Если передумал, напиши /cancel, чтобы вернуться в начало")


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
