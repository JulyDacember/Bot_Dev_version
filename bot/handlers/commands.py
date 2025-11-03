from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode, ShowMode
from fluent.runtime import FluentLocalization
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from state_machines.templates import CreateByTemplate
from database.models import Person
from database.models.requisites import Requisites
from database.models.refund import Refund
from utils.escape import escape_mdv2

router = Router()


@router.message(CommandStart())
async def start(msg: Message, l10n: FluentLocalization, session: AsyncSession):
    # Ensure user exists in DB
    tg_id = msg.from_user.id if msg.from_user else None
    full_name = msg.from_user.full_name if msg.from_user else ""
    if tg_id:
        res = await session.execute(select(Person).where(Person.telegram_id == tg_id))
        person = res.scalar_one_or_none()
        if person is None:
            person = Person(telegram_id=tg_id, full_name=full_name)
            session.add(person)
            await session.commit()
    await msg.answer(escape_mdv2(l10n.format_value("start-msg")))


@router.message(Command('create_document'))
async def choose_template(_: Message, dialog_manager: DialogManager):
	""" Ask for a template for creation """
	await dialog_manager.start(
		CreateByTemplate.CHOOSE_TEMPLATE,
		mode=StartMode.RESET_STACK,
		show_mode=ShowMode.DELETE_AND_SEND
	)


@router.message(Command('add_requisites'))
async def add_requisites(msg: Message, session: AsyncSession):
    if not msg.from_user:
        return
    tg_id = msg.from_user.id
    details = (msg.text or '').partition(' ')[2].strip()
    if not details:
        await msg.answer(escape_mdv2("Укажите реквизиты после команды, например: /add_requisites 40817..."))
        return
    res = await session.execute(select(Person).where(Person.telegram_id == tg_id))
    person = res.scalar_one_or_none()
    if person is None:
        person = Person(telegram_id=tg_id, full_name=msg.from_user.full_name)
        session.add(person)
        await session.flush()
    # upsert requisites
    req_res = await session.execute(select(Requisites).where(Requisites.person == person))
    req = req_res.scalar_one_or_none()
    if req is None:
        req = Requisites(details=details, person=person)
        session.add(req)
    else:
        req.details = details
    await session.commit()
    await msg.answer(escape_mdv2("Реквизиты сохранены."))


@router.message(Command('my_requisites'))
async def my_requisites(msg: Message, session: AsyncSession):
    if not msg.from_user:
        return
    tg_id = msg.from_user.id
    res = await session.execute(select(Person).where(Person.telegram_id == tg_id))
    person = res.scalar_one_or_none()
    if not person:
        await msg.answer(escape_mdv2("Пользователь не найден. Отправьте /start"))
        return
    req_res = await session.execute(select(Requisites).where(Requisites.person == person))
    req = req_res.scalar_one_or_none()
    if not req:
        await msg.answer(escape_mdv2("Реквизиты не указаны. Используйте /add_requisites ..."))
        return
    await msg.answer(escape_mdv2(f"Ваши реквизиты: {req.details}"))


@router.message(Command('create_refund'))
async def create_refund(msg: Message, session: AsyncSession):
    if not msg.from_user:
        return
    tg_id = msg.from_user.id
    args = (msg.text or '').partition(' ')[2].strip()
    if not args:
        await msg.answer(escape_mdv2("Укажите название возврата после команды, например: /create_refund Товар"))
        return
    res = await session.execute(select(Person).where(Person.telegram_id == tg_id))
    person = res.scalar_one_or_none()
    if person is None:
        person = Person(telegram_id=tg_id, full_name=msg.from_user.full_name)
        session.add(person)
        await session.flush()
    refund = Refund(name=args, description=None, customer=person, payment_id=1)
    session.add(refund)
    await session.commit()
    await msg.answer(escape_mdv2("Заявка на возврат создана."))


@router.message(Command('my_refunds'))
async def my_refunds(msg: Message, session: AsyncSession):
    if not msg.from_user:
        return
    tg_id = msg.from_user.id
    res = await session.execute(select(Person).where(Person.telegram_id == tg_id))
    person = res.scalar_one_or_none()
    if not person:
        await msg.answer(escape_mdv2("Пользователь не найден. Отправьте /start"))
        return
    await person.awaitable_attrs.refunds
    refunds = person.refunds
    if not refunds:
        await msg.answer(escape_mdv2("Возвраты не найдены."))
        return
    lines = [f"#{r.id}: {r.name}" for r in refunds]
    await msg.answer(escape_mdv2("Ваши возвраты:\n" + "\n".join(lines)))
