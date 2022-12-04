import logging
import pickle
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from osnova import Token

storage = MemoryStorage()
bot = Bot(Token)
dp = Dispatcher(bot, storage=storage)


class Notification:
    def __init__(self):
        self.name = ''
        self.date = ''
        self.text = ''

    def state_name(self, value):
        self.name = value

    def state_date(self, value):
        self.date = value

    def state_text(self, value):
        self.text = value


class NewUser(StatesGroup):
    name = State()


new = Notification()


class NewState(StatesGroup):
    name = State()
    date = State()
    text = State()


class DeleteState(StatesGroup):
    name = State()
    change = State()
    delete = State()
    swap = State()
    swapname = State()
    swapdate = State()
    swaptext = State()


@dp.message_handler(commands=['help'])
async def process_start_command(message: types.Message):
    await message.answer('Это лучший бот для заметочек евер мейд\n'
                           '/newnote - создать новую заметочку'
                           '/mynotes - чтобы посмтореть ваши заметочки\n'
                           '/change - чтобы поменять заметку\n'
                           '/cancel - чтобы выйти из процесса создания или удаления чего либо\n'
                           '/delete - удалить свой профиль со всеми данными\n')


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    with open('data.dat', 'rb') as f:
        data_storage = pickle.load(f)
    if message.chat.id in data_storage.keys():
        await message.answer("С возвращением {}".format(data_storage[message.chat.id]['name']))
        await message.answer("Чтобы посмотреть, что умеет этот бот, нажмите /help \n")
        return
    else:
        await NewUser.name.set()
        await message.answer("Введите свое имя\n")


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    await state.finish()
    await message.reply('Cancelled.')


@dp.message_handler(commands='delete')
@dp.message_handler(Text(equals='delete', ignore_case=True))
async def delete_user(message: types.Message, state: FSMContext):
    with open('data.dat', 'rb') as f:
        data_storage = pickle.load(f)
    data_storage.pop(message.chat.id)
    with open('data.dat', 'wb') as f:
        pickle.dump(data_storage, f)
    await message.answer('ну и пожалуйста')


@dp.message_handler(state=NewUser.name)
async def process_name(message: types.Message, state: FSMContext):
    with open('data.dat', 'rb') as f:
        data_storage = pickle.load(f)
    data_storage[message.chat.id] = {'name': message.text, 'notes': []}
    await message.answer("Добро пожаловать, {}".format(data_storage[message.chat.id]['name']))
    with open('data.dat', 'wb') as f:
        pickle.dump(data_storage, f)
    await message.answer("Чтобы посмотреть, что умеет этот бот, нажмите /help \n")
    await state.finish()


@dp.message_handler(commands=['newnote'])
async def process_new_note(message: types.Message):
    await NewState.name.set()
    await message.answer("Введите название\n")


@dp.message_handler(state=NewState.name)
async def state(message: types.Message, state: FSMContext):
    global new
    new.state_name(message.text)
    await message.answer("Введите дату\n")
    await NewState.next()


@dp.message_handler(state=NewState.date)
async def state(message: types.Message, state: FSMContext):
    global new
    new.state_date(message.text)
    await message.answer("Введите описание\n")
    await NewState.next()


@dp.message_handler(state=NewState.text)
async def state(message: types.Message, state: FSMContext):
    global new
    new.state_text(message.text)
    with open('data.dat', 'rb') as f:
        data_storage = pickle.load(f)
    data_storage[message.chat.id]['notes'].append(new)
    with open('data.dat', 'wb') as f:
        pickle.dump(data_storage, f)
    await message.answer('Успешно')
    await message.answer('/newnote - создать новую заметочку'
                         '/mynotes - чтобы посмтореть ваши заметочки\n'
                         '/change - чтобы поменять заметку\n'
                         '/cancel - чтобы выйти из процесса создания или удаления чего либо\n'
                         '/delete - удалить свой профиль со всеми данными\n')
    await state.finish()


@dp.message_handler(commands=['mynotes'])
async def process_show_note(message: types.Message):
    with open('data.dat', 'rb') as f:
        stack = pickle.load(f)
    count = 1
    for i in stack[message.chat.id]['notes']:
        await message.answer("{} {} {} {}".format(count, i.name, i.date, i.text))
        count += 1


@dp.message_handler(commands=['change'])
async def process_new_note(message: types.Message):
    await DeleteState.name.set()
    await message.answer("Введите название заметки, которую хотите поменять")


@dp.message_handler(state=DeleteState.name)
async def change_name(message: types.Message, state: FSMContext):
    st = message.text
    with open('data.dat', 'rb') as f:
        stack = pickle.load(f)
    list_of_similar = {}
    count = 1
    for i in stack[message.chat.id]['notes']:
        if st in i.name:
            list_of_similar[count] = {'vhzhd': stack[message.chat.id]['notes'].index(i), 'cont': i}
            count += 1
    async with state.proxy() as data:
        data['template'] = list_of_similar
    new_count = 1
    for i in list_of_similar.keys():
        await message.answer("{} {}".format(new_count, list_of_similar[i]['cont'].name))
        new_count += 1
    await message.answer('Результаты по поиску {}\n Введите номер заметки,которую хотите поменять'.format(message.text))
    await DeleteState.next()


list1 = []
for i in range(0, 10):
    list1.append(str(i))


@dp.message_handler(state=DeleteState.change)
@dp.message_handler(Text(contains=list1))
async def state(message: types.Message, state: FSMContext):
    num = int(message.text)
    async with state.proxy() as data:
        if not (num in data['template'].keys()):
            await message.answer('Неверно')
            return
        data['idx'] = num
    await message.answer('успешно')
    await DeleteState.next()
    await message.answer('/del - удалить выбранную заметочку\n'
                         '/swap - изменить выбранную заметку\n')


@dp.message_handler(state=DeleteState.delete, commands='del')
async def state(message: types.Message, state: FSMContext):
    with open('data.dat', 'rb') as f:
        stack = pickle.load(f)
    async with state.proxy() as data:
        idx = data['idx']
    stack[message.chat.id]['notes'].pop(idx - 1)
    await message.answer("Успешно")
    with open('data.dat', 'wb') as f:
        pickle.dump(stack, f)
    await state.finish()
    await message.answer('/newnote - создать новую заметочку\n'
                         '/mynotes - чтобы посмтореть ваши заметочки\n'
                         '/change - чтобы поменять заметку\n'
                         '/cancel - чтобы выйти из процесса создания или удаления чего либо\n'
                         '/delete - удалить свой профиль со всеми данными\n')


@dp.message_handler(state=DeleteState.delete, commands='swap')
async def state(message: types.Message, state: FSMContext):
    await DeleteState.swap.set()
    await message.answer('/swapdate - чтобы поменять дату\n'
                         '/swapname - чтобы поменять имя\n'
                         '/swaptext - чтобы поменять описание\n')


@dp.message_handler(state=DeleteState.swap, commands='swapdate')
async def state(message: types.Message, state: FSMContext):
    await DeleteState.swapdate.set()
    await message.answer('Введите новую дату')


@dp.message_handler(state=DeleteState.swapdate)
async def state(message: types.Message, state: FSMContext):
    with open('data.dat', 'rb') as f:
        stack = pickle.load(f)
    async with state.proxy() as data:
        idx = data['idx']
    stack[message.chat.id]['notes'][idx - 1].state_date(message.text)
    with open('data.dat', 'wb') as f:
        pickle.dump(stack, f)
    await state.finish()
    await message.answer("Успешно")
    await message.answer('/newnote - создать новую заметочку\n'
                         '/mynotes - чтобы посмтореть ваши заметочки\n'
                         '/change - чтобы поменять заметку\n'
                         '/cancel - чтобы выйти из процесса создания или удаления чего либо\n'
                         '/delete - удалить свой профиль со всеми данными\n')


@dp.message_handler(state=DeleteState.swap, commands='swapname')
async def state(message: types.Message, state: FSMContext):
    await DeleteState.swapname.set()
    await message.answer('Введите новое имя')


@dp.message_handler(state=DeleteState.swapname)
async def state(message: types.Message, state: FSMContext):
    with open('data.dat', 'rb') as f:
        stack = pickle.load(f)
    async with state.proxy() as data:
        idx = data['idx']
    stack[message.chat.id]['notes'][idx - 1].state_name(message.text)
    with open('data.dat', 'wb') as f:
        pickle.dump(stack, f)
    await state.finish()
    await message.answer("Успешно")
    await message.answer('/newnote - создать новую заметочку\n'
                         '/mynotes - чтобы посмтореть ваши заметочки\n'
                         '/change - чтобы поменять заметку\n'
                         '/cancel - чтобы выйти из процесса создания или удаления чего либо\n'
                         '/delete - удалить свой профиль со всеми данными\n')


@dp.message_handler(state=DeleteState.swap, commands='swaptext')
async def state(message: types.Message, state: FSMContext):
    await DeleteState.swaptext.set()
    await message.answer('Введите новое описание')


@dp.message_handler(state=DeleteState.swaptext)
async def state(message: types.Message, state: FSMContext):
    with open('data.dat', 'rb') as f:
        stack = pickle.load(f)
    async with state.proxy() as data:
        idx = data['idx']
    stack[message.chat.id]['notes'][idx - 1].state_text(message.text)
    with open('data.dat', 'wb') as f:
        pickle.dump(stack, f)
    await state.finish()
    await message.answer("Успешно")
    await message.answer('/newnote - создать новую заметочку\n'
                         '/mynotes - чтобы посмтореть ваши заметочки\n'
                         '/change - чтобы поменять заметку\n'
                         '/cancel - чтобы выйти из процесса создания или удаления чего либо\n'
                         '/delete - удалить свой профиль со всеми данными\n')


if __name__ == "__main__":
    executor.start_polling(dp)
