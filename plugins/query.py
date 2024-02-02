import asyncio, re, ast, time, math, logging, random, pyrogram, shutil, psutil 

# Pyrogram Functions
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from pyrogram import Client, filters, enums 
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid

# Helper Function
from Script import script
from utils import get_size, is_subscribed, get_poster, search_gagala, temp, get_settings, save_group_settings, get_shortlink, get_time, humanbytes 
from .ExtraMods.carbon import make_carbon

# Database Function 
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, make_inactive
from database.ia_filterdb import Media, get_file_details, get_search_results
from database.filters_mdb import del_all, find_filter, get_filters
from database.gfilters_mdb import find_gfilter, get_gfilters
from database.users_chats_db import db

# Image Editor Function
from image.edit_1 import bright, mix, black_white, g_blur, normal_blur, box_blur
from image.edit_2 import circle_with_bg, circle_without_bg, sticker, edge_curved, contrast, sepia_mode, pencil, cartoon                             
from image.edit_3 import green_border, blue_border, black_border, red_border
from image.edit_4 import rotate_90, rotate_180, rotate_270, inverted, round_sticker, removebg_white, removebg_plain, removebg_sticker
from image.edit_5 import normalglitch_1, normalglitch_2, normalglitch_3, normalglitch_4, normalglitch_5, scanlineglitch_1, scanlineglitch_2, scanlineglitch_3, scanlineglitch_4, scanlineglitch_5

# Configuration
from info import ADMINS, AUTH_CHANNEL, AUTH_USERS, CUSTOM_FILE_CAPTION, AUTH_GROUPS, P_TTI_SHOW_OFF, PICS, IMDB, PM_IMDB, SINGLE_BUTTON, PROTECT_CONTENT, \
    SPELL_CHECK_REPLY, IMDB_TEMPLATE, IMDB_DELET_TIME, START_MESSAGE, PMFILTER, G_FILTER, BUTTON_LOCK, BUTTON_LOCK_TEXT, SHORT_URL, SHORT_API


logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)



@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
        
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type
        if chat_type == enums.ChatType.PRIVATE:
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    return await query.message.edit_text("Make Sure I'm Present In Your Group!!", quote=True)
            else:
                return await query.message.edit_text("I'm Not Connected To Any Groups!\ncheck /Connections Or Connect To Any Groups", quote=True)
        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            title = query.message.chat.title
        else: return
        st = await client.get_chat_member(grp_id, userid)
        if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS): await del_all(query.message, grp_id, title)
        else: await query.answer("You Need To Be Group Owner Or An Auth User To Do That!", show_alert=True)
        
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type
        if chat_type == enums.ChatType.PRIVATE:
            await query.message.reply_to_message.delete()
            await query.message.delete()
        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
                await query.message.delete()
                try: await query.message.reply_to_message.delete()
                except: pass
            else: await query.answer("That's Not For You Buddy", show_alert=True)
            
    elif "groupcb" in query.data:
        group_id = query.data.split(":")[1]
        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id
        if act == "":
            stat = "Connect"
            cb = "connectcb"
        else:
            stat = "Disconnect"
            cb = "disconnect"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
            InlineKeyboardButton("Delete", callback_data=f"deletecb:{group_id}")
            ],[
            InlineKeyboardButton("Back", callback_data="backcb")]
        ])
        await query.message.edit_text(f"Group Name:- **{title}**\nGroup Id:- `{group_id}`", reply_markup=keyboard, parse_mode=enums.ParseMode.MARKDOWN)
      
    elif "connectcb" in query.data:
        group_id = query.data.split(":")[1]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id
        mkact = await make_active(str(user_id), str(group_id))
        if mkact: await query.message.edit_text(f"Connected To: **{title}**", parse_mode=enums.ParseMode.MARKDOWN,)
        else: await query.message.edit_text('Some Error Occurred!!', parse_mode="md")
       
    elif "disconnect" in query.data:
        group_id = query.data.split(":")[1]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id
        mkinact = await make_inactive(str(user_id))
        if mkinact: await query.message.edit_text(f"Disconnected From **{title}**", parse_mode=enums.ParseMode.MARKDOWN)
        else: await query.message.edit_text(f"Some Error Occurred!!", parse_mode=enums.ParseMode.MARKDOWN)
      
    elif "deletecb" in query.data:
        user_id = query.from_user.id
        group_id = query.data.split(":")[1]
        delcon = await delete_connection(str(user_id), str(group_id))
        if delcon: await query.message.edit_text("Successfully Deleted Connection")
        else: await query.message.edit_text(f"Some Error Occurred!!", parse_mode=enums.ParseMode.MARKDOWN)
       
    elif query.data == "backcb":
        userid = query.from_user.id
        groupids = await all_connections(str(userid))
        if groupids is None:
            return await query.message.edit_text("There Are No Active Connections!! Connect To Some Groups First.")
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append([InlineKeyboardButton(f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}")])
            except: pass
        if buttons: await query.message.edit_text("Your Connected Group Details ;\n\n", reply_markup=InlineKeyboardMarkup(buttons))
            
    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]        
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)       
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
            
    elif "galert" in query.data:
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]             
        reply_text, btn, alerts, fileid = await find_gfilter("gfilters", keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
    
    if query.data.startswith("pmfile"):
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_: return await query.answer('No Such File Exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = f_caption = f"{title}"
        if CUSTOM_FILE_CAPTION:
            try: f_caption = CUSTOM_FILE_CAPTION.format(mention=query.from_user.mention, file_name='' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)                                                                                                      
            except Exception as e: logger.exception(e)
        try:                  
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                return await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
            else:
                await client.send_cached_media(chat_id=query.from_user.id, file_id=file_id, caption=f_caption, protect_content=True if ident == "pmfilep" else False)                       
        except Exception as e:
            await query.answer(f"𝘌𝘳𝘰𝘳𝘳 {e}", show_alert=True)
        
    if query.data.startswith("file"):        
        ident, req, file_id = query.data.split("#")
        if BUTTON_LOCK:
            if int(req) not in [query.from_user.id, 0]:
                return await query.answer(BUTTON_LOCK_TEXT.format(query=query.from_user.first_name), show_alert=True)
        files_ = await get_file_details(file_id)
        if not files_: return await query.answer('No Such File Exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = f_caption = f"{title}"
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try: f_caption = CUSTOM_FILE_CAPTION.format(mention=query.from_user.mention, file_name='' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)                               
            except Exception as e: logger.exception(e)
        try:
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                return await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
            elif settings['botpm']:
                return await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
            else:
                await client.send_cached_media(chat_id=query.from_user.id, file_id=file_id, caption=f_caption, protect_content=True if ident == "filep" else False)
                await query.answer('𝘍𝘪𝘭𝘦𝘴 𝘏𝘢𝘷𝘦 𝘉𝘦𝘦𝘯 𝘚𝘦𝘯𝘵 𝘛𝘰 𝘠𝘰𝘶𝘳 𝘐𝘯𝘣𝘰𝘹', show_alert=True)
        except UserIsBlocked:
            await query.answer('𝘜𝘯𝘣𝘭𝘰𝘤𝘬 𝘔𝘦', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
        except Exception as e:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
     
    elif query.data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            return await query.answer("𝘐 𝘢𝘥𝘮𝘪𝘳𝘦 𝘺𝘰𝘶𝘳 𝘤𝘭𝘦𝘷𝘦𝘳𝘯𝘦𝘴𝘴．𝘋𝘰𝘯𝘵 𝘖𝘷𝘦𝘳𝘋𝘰 𝘐𝘵", show_alert=True)
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_: return await query.answer('No FILE Matching your request....')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = f_caption = f"{title}"
        if CUSTOM_FILE_CAPTION:
            try: f_caption = CUSTOM_FILE_CAPTION.format(mention=query.from_user.mention, file_name='' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)  
            except Exception as e: logger.exception(e)
        await client.send_cached_media(chat_id=query.from_user.id, file_id=file_id, caption=f_caption, protect_content=True if ident == 'checksubp' else False)

    elif query.data == "removebg":
        buttons = [[
            InlineKeyboardButton(text="𝘞𝘪𝘵𝘩 𝘞𝘩𝘪𝘵𝘦 𝘉𝘎", callback_data="rmbgwhite"),
            InlineKeyboardButton(text="𝘞𝘪𝘵𝘩𝘰𝘶𝘵 𝘉𝘎", callback_data="rmbgplain"),
            ],[
            InlineKeyboardButton(text="𝘚𝘵𝘪𝘤𝘬𝘦𝘳", callback_data="rmbgsticker"),
            ],[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='photo')
        ]]
        await query.message.edit_text("**Select Required Mode**", reply_markup=InlineKeyboardMarkup(buttons))
            
    elif query.data == "stick":
        buttons = [[
            InlineKeyboardButton(text="𝘕𝘰𝘳𝘮𝘢𝘭", callback_data="stkr"),
            InlineKeyboardButton(text="𝘌𝘥𝘨𝘦 𝘊𝘶𝘳𝘷𝘦𝘥", callback_data="cur_ved"),
            ],[                    
            InlineKeyboardButton(text="𝘊𝘪𝘳𝘤𝘭𝘦", callback_data="circle_sticker")
            ],[
            InlineKeyboardButton('𝘉𝘢𝘤𝘬', callback_data='photo')
        ]]              
        await query.message.edit("**Select A Type**", reply_markup=InlineKeyboardMarkup(buttons))          
            
    elif query.data == "rotate":
        buttons = [[
            InlineKeyboardButton(text="180", callback_data="180"),
            InlineKeyboardButton(text="90", callback_data="90")
            ],[
            InlineKeyboardButton(text="270", callback_data="270")
            ],[
            InlineKeyboardButton('𝘉𝘢𝘤𝘬', callback_data='photo')
        ]]
        await query.message.edit_text("**Select The Degree**", reply_markup=InlineKeyboardMarkup(buttons))
            
    elif query.data == "glitch":
        buttons = [[
            InlineKeyboardButton(text="𝘕𝘰𝘳𝘮𝘢𝘭", callback_data="normalglitch"),
            InlineKeyboardButton(text="𝘚𝘤𝘢𝘯 𝘓𝘪𝘯𝘦𝘴", callback_data="scanlineglitch")
            ],[
            InlineKeyboardButton('𝘉𝘢𝘤𝘬', callback_data='photo')
        ]]
        await query.message.edit_text("**Select Required Mode**", reply_markup=InlineKeyboardMarkup(buttons))
            
    elif query.data == "normalglitch":
        buttons = [[
            InlineKeyboardButton(text="1", callback_data="normalglitch1"),
            InlineKeyboardButton(text="2", callback_data="normalglitch2"),
            InlineKeyboardButton(text="3", callback_data="normalglitch3"),
            ],[
            InlineKeyboardButton(text="4", callback_data="normalglitch4"),
            InlineKeyboardButton(text="5", callback_data="normalglitch5"),
            ],[
            InlineKeyboardButton('𝘉𝘢𝘤𝘬', callback_data='glitch')
            ]]
        await query.message.edit_text(text="**Select Glitch Power Level**", reply_markup=InlineKeyboardMarkup(buttons))
           
    elif query.data == "scanlineglitch":
        buttons = [[
            InlineKeyboardButton(text="1", callback_data="scanlineglitch1"),
            InlineKeyboardButton(text="2", callback_data="scanlineglitch2"),
            InlineKeyboardButton(text="3", callback_data="scanlineglitch3"),
            ],[
            InlineKeyboardButton(text="4", callback_data="scanlineglitch4"),
            InlineKeyboardButton(text="5", callback_data="scanlineglitch5"),
            ],[
            InlineKeyboardButton('𝘉𝘈𝘊𝘒', callback_data='glitch')
        ]]
        await query.message.edit_text("**Select Glitch Power Level**", reply_markup=InlineKeyboardMarkup(buttons))
            
    elif query.data == "blur":
        buttons = [[
            InlineKeyboardButton(text="𝘉𝘰𝘹", callback_data="box"),
            InlineKeyboardButton(text="𝘕𝘰𝘳𝘮𝘢𝘭", callback_data="normal"),
            ],[
            InlineKeyboardButton(text="𝘎𝘢𝘴", callback_data="gas")
            ],[
            InlineKeyboardButton('𝘉𝘢𝘤𝘬', callback_data='photo')
        ]]
        await query.message.edit("**Select A Type**", reply_markup=InlineKeyboardMarkup(buttons))
            
    elif query.data == "circle":
        buttons = [[
            InlineKeyboardButton(text="𝘉𝘎 𝘐𝘯𝘤𝘭𝘶𝘥𝘦𝘥", callback_data="circlewithbg"),
            InlineKeyboardButton(text="𝘉𝘎 𝘌𝘹𝘤𝘭𝘶𝘥𝘦𝘥", callback_data="circlewithoutbg"),
            ],[
            InlineKeyboardButton('𝘉𝘢𝘤𝘬', callback_data='photo')
        ]]
        await query.message.edit_text("**Select Required Mode**", reply_markup=InlineKeyboardMarkup(buttons))
            
    elif query.data == "border":
        buttons = [[
            InlineKeyboardButton(text="𝘙𝘦𝘥", callback_data="red"),
            InlineKeyboardButton(text="𝘎𝘳𝘦𝘦𝘯", callback_data="green"),
            ],[
            InlineKeyboardButton(text="𝘉𝘭𝘢𝘤𝘬", callback_data="black"),
            InlineKeyboardButton(text="𝘉𝘭𝘶𝘦", callback_data="blue"),
            ],[                    
            InlineKeyboardButton('𝘉𝘢𝘤𝘬', callback_data='photo')   
        ]]           
        await query.message.edit("**Select Border**", reply_markup=InlineKeyboardMarkup(buttons))
   
    elif query.data == "photo":
        buttons = [[
            InlineKeyboardButton(text="𝘉𝘳𝘪𝘨𝘩𝘵", callback_data="bright"),
            InlineKeyboardButton(text="𝘔𝘪𝘹", callback_data="mix"),
            InlineKeyboardButton(text="𝘉 𝘯 𝘞", callback_data="b|w"),
            ],[
            InlineKeyboardButton(text="𝘊𝘪𝘳𝘤𝘭𝘦", callback_data="circle"),
            InlineKeyboardButton(text="𝘉𝘭𝘶𝘳", callback_data="blur"),
            InlineKeyboardButton(text="𝘉𝘰𝘳𝘥𝘦𝘳", callback_data="border"),
            ],[
            InlineKeyboardButton(text="𝘚𝘵𝘪𝘤𝘬𝘦𝘳", callback_data="stick"),
            InlineKeyboardButton(text="𝘙𝘰𝘵𝘢𝘵𝘦", callback_data="rotate"),
            InlineKeyboardButton(text="𝘊𝘰𝘯𝘵𝘳𝘢𝘴𝘵", callback_data="contrast"),
            ],[
            InlineKeyboardButton(text="𝘚𝘦𝘱𝘪𝘢", callback_data="sepia"),
            InlineKeyboardButton(text="𝘗𝘦𝘯𝘤𝘪𝘭", callback_data="pencil"),
            InlineKeyboardButton(text="𝘊𝘢𝘳𝘵𝘰𝘰𝘯", callback_data="cartoon"),
            ],[
            InlineKeyboardButton(text="𝘐𝘯𝘷𝘦𝘳𝘵𝘦𝘥", callback_data="inverted"),
            InlineKeyboardButton(text="𝘎𝘭𝘪𝘵𝘤𝘩", callback_data="glitch"),
            InlineKeyboardButton(text="𝘉𝘎 𝘦𝘹𝘤𝘭𝘶𝘥𝘦𝘥", callback_data="removebg")
            ],[
            InlineKeyboardButton(text="𝘊𝘭𝘰𝘴𝘦", callback_data="close_data")
        ]]
        await query.message.edit_text("𝘊𝘩𝘰𝘰𝘴𝘦 𝘛𝘩𝘦 𝘔𝘰𝘥𝘦 𝘛𝘩𝘢𝘵 𝘉𝘦𝘴𝘵 𝘚𝘶𝘪𝘵𝘴 𝘠𝘰𝘶𝘳 𝘕𝘦𝘦𝘥𝘴", reply_markup=InlineKeyboardMarkup(buttons))
               
    elif query.data == "bright":
        await bright(client, query.message)
    elif query.data == "mix":
        await mix(client, query.message)
    elif query.data == "b|w":
        await black_white(client, query.message)
    elif query.data == "circlewithbg":
        await circle_with_bg(client, query.message)
    elif query.data == "circlewithoutbg":
        await circle_without_bg(client, query.message)
    elif query.data == "green":
        await green_border(client, query.message)
    elif query.data == "blue":
        await blue_border(client, query.message)
    elif query.data == "red":
        await red_border(client, query.message)
    elif query.data == "black":
        await black_border(client, query.message)
    elif query.data == "circle_sticker":
        await round_sticker(client, query.message)
    elif query.data == "inverted":
        await inverted(client, query.message)
    elif query.data == "stkr":
        await sticker(client, query.message)
    elif query.data == "cur_ved":
        await edge_curved(client, query.message)
    elif query.data == "90":
        await rotate_90(client, query.message)
    elif query.data == "180":
        await rotate_180(client, query.message)
    elif query.data == "270":
        await rotate_270(client, query.message)
    elif query.data == "contrast":
        await contrast(client, query.message)
    elif query.data == "box":
        await box_blur(client, query.message)
    elif query.data == "gas":
        await g_blur(client, query.message)
    elif query.data == "normal":
        await normal_blur(client, query.message)
    elif query.data == "sepia":
        await sepia_mode(client, query.message)
    elif query.data == "pencil":
        await pencil(client, query.message)
    elif query.data == "cartoon":
        await cartoon(client, query.message)
    elif query.data == "normalglitch1":
        await normalglitch_1(client, query.message)
    elif query.data == "normalglitch2":
        await normalglitch_2(client, query.message)
    elif query.data == "normalglitch3":
        await normalglitch_3(client, query.message)
    elif query.data == "normalglitch4":
        await normalglitch_4(client, query.message)
    elif query.data == "normalglitch5":
        await normalglitch_5(client, query.message)
    elif query.data == "scanlineglitch1":
        await scanlineglitch_1(client, query.message)
    elif query.data == "scanlineglitch2":
        await scanlineglitch_2(client, query.message)
    elif query.data == "scanlineglitch3":
        await scanlineglitch_3(client, query.message)
    elif query.data == "scanlineglitch4":
        await scanlineglitch_4(client, query.message)
    elif query.data == "scanlineglitch5":
        await scanlineglitch_5(client, query.message)
    elif query.data == "rmbgwhite":
        await removebg_white(client, query.message)
    elif query.data == "rmbgplain":
        await removebg_plain(client, query.message)
    elif query.data == "rmbgsticker":
        await removebg_sticker(client, query.message)
    elif query.data == "pages":
        await query.answer("𝘊𝘶𝘳𝘪𝘰𝘴𝘪𝘵𝘺 𝘱𝘰𝘴𝘴𝘦𝘴𝘴𝘦𝘴 𝘢 𝘤𝘦𝘳𝘵𝘢𝘪𝘯 𝘫𝘦 𝘯𝘢𝘪 𝘴𝘢𝘪𝘴 𝘲𝘶𝘰𝘪 𝘥𝘰𝘦𝘴𝘯𝘵 𝘪𝘵", show_alert=True)
    elif query.data == "howdl":
        try: await query.answer(script.HOW_TO_DOWNLOAD.format(query.from_user.first_name), show_alert=True)
        except: await query.message.edit(script.HOW_TO_DOWNLOAD.format(query.from_user.first_name))

    elif query.data == "start":                        
        buttons = [[
            InlineKeyboardButton("🔮𝘉𝘦 𝘖𝘧 𝘚𝘦𝘳𝘷𝘪𝘤𝘦🔮", url=f"http://t.me/{temp.U_NAME}?startgroup=true")
            ],[
            InlineKeyboardButton("🔮𝘚𝘶𝘳𝘷𝘦𝘺𝘪𝘯𝘨🔮", switch_inline_query_current_chat=''), 
            InlineKeyboardButton("🔮𝘔𝘰𝘳𝘥𝘦𝘯𝘪𝘻𝘦𝘥🔮", url="https://t.me/mkn_bots_updates")
            ],[      
            InlineKeyboardButton("🔮𝘈𝘴𝘴𝘪𝘴𝘵𝘢𝘯𝘤𝘦🔮", callback_data="help"),
            InlineKeyboardButton("🔮𝘎𝘰𝘑𝘰🔮", callback_data="about")
        ]]
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), START_MESSAGE.format(user=query.from_user.mention, bot=client.mention), enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))
       
    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton('🔮𝘔𝘺 𝘔𝘢𝘴𝘵𝘦𝘳🔮', 'admin')            
            ],[
            InlineKeyboardButton('🔮𝘍𝘪𝘭𝘵𝘦𝘳 𝘗𝘢𝘯𝘦𝘭🔮', 'openfilter'),
            InlineKeyboardButton('🔮𝘊𝘰𝘯𝘯𝘦𝘤𝘵🔮', 'coct')
            ],[                       
            InlineKeyboardButton('🔮𝘕𝘦𝘸 𝘚𝘱𝘦𝘤𝘪𝘧𝘪𝘤𝘴🔮', 'newdata'),
            InlineKeyboardButton('🔮𝘌𝘟𝘛 𝘔𝘰𝘥🔮', 'extmod')
            ],[           
            InlineKeyboardButton('🔮𝘎𝘳𝘰𝘶𝘱 𝘌𝘹𝘦𝘤𝘶𝘵𝘪𝘷𝘦𝘴🔮', 'gpmanager'), 
            InlineKeyboardButton('🔮𝘈𝘣𝘰𝘶𝘵 𝘔𝘦🔮', 'stats')
            ],[
            InlineKeyboardButton('🔮𝘊𝘭𝘰𝘴𝘦🔮', 'close_data'),
            InlineKeyboardButton('🔮𝘉𝘢𝘤𝘬🔮', 'start')           
        ]]
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.HELP_TXT.format(query.from_user.mention), enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))     
        
    elif query.data == "about":
        buttons= [[
            InlineKeyboardButton('🔮𝘔𝘪𝘤𝘳𝘰𝘊𝘰𝘥𝘦🔮', 'source')
            ],[
            InlineKeyboardButton('🔮𝘊𝘭𝘰𝘴𝘦🔮', 'close_data'),
            InlineKeyboardButton('🔮𝘉𝘢𝘤𝘬🔮', 'start')          
        ]]
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.ABOUT_TXT.format(temp.B_NAME), enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))
        
    elif query.data == "source":
        buttons = [[
            InlineKeyboardButton('🔮𝘗𝘳𝘰𝘨𝘳𝘢𝘮𝘓𝘪𝘯𝘦🔮', url='https://telegra.ph/Clarification-Regarding-Ownership-of-a-Bot-02-02')
            ],[
            InlineKeyboardButton('🔮𝘉𝘢𝘤𝘬🔮', 'about')
        ]]
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.SOURCE_TXT, enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))
      
    elif query.data == "admin":
        buttons = [[
            InlineKeyboardButton('🔮𝘊𝘭𝘰𝘴𝘦🔮', 'close_data'),
            InlineKeyboardButton('🔮𝘉𝘢𝘤𝘬🔮', 'help')           
        ]]
        if query.from_user.id not in ADMINS:
            return await query.answer("𝘖𝘯𝘭𝘺 𝘔𝘺 𝘔𝘢𝘴𝘵𝘦𝘳 𝘊𝘢𝘯 𝘗𝘦𝘳𝘧𝘰𝘳𝘮 𝘛𝘩𝘪𝘴", show_alert=True)
        await query.message.edit("𝘞𝘢𝘪𝘵 𝘍𝘪𝘍𝘛𝘦𝘦𝘯 𝘚𝘦𝘤𝘰𝘯𝘥𝘴...")
        total, used, free = shutil.disk_usage(".")
        stats = script.SERVER_STATS.format(get_time(time.time() - client.uptime), psutil.cpu_percent(), psutil.virtual_memory().percent, humanbytes(total), humanbytes(used), psutil.disk_usage('/').percent, humanbytes(free))            
        stats_pic = await make_carbon(stats, True)
        await query.edit_message_media(InputMediaPhoto(stats_pic, script.ADMIN_TXT, enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))
        
    elif query.data == "openfilter":
        buttons = [[
            InlineKeyboardButton('🔮𝘈𝘶𝘵𝘰𝘍𝘪𝘭𝘵𝘦𝘳🔮', 'autofilter'),
            InlineKeyboardButton('🔮𝘔𝘢𝘯𝘶𝘢𝘭𝘍𝘪𝘭𝘵𝘦𝘳🔮', 'manuelfilter')
            ],[
            InlineKeyboardButton('🔮𝘎𝘭𝘰𝘣𝘢𝘭𝘍𝘪𝘭𝘵𝘦𝘳🔮', 'globalfilter')
            ],[
            InlineKeyboardButton('🔮𝘊𝘭𝘰𝘴𝘦🔮', 'close_data'),
            InlineKeyboardButton('🔮𝘉𝘢𝘤𝘬🔮', 'help')           
        ]]
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.FILTER_TXT, enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))
        
    elif query.data == "autofilter":
        buttons = [[
            InlineKeyboardButton('🔮𝘊𝘭𝘰𝘴𝘦🔮', 'close_data'),
            InlineKeyboardButton('🔮𝘉𝘢𝘤𝘬🔮', 'openfilter')           
        ]]
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.AUTOFILTER_TXT, enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))
        
    elif query.data == "manuelfilter":
        buttons = [[
            InlineKeyboardButton('🔮𝘉𝘶𝘵𝘵𝘰𝘯𝘍𝘰𝘳𝘮𝘢𝘵🔮', 'button')
            ],[
            InlineKeyboardButton('🔮𝘊𝘭𝘰𝘴𝘦🔮', 'close_data'),
            InlineKeyboardButton('🔮𝘉𝘢𝘤𝘬🔮', 'openfilter')           
        ]]
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.MANUELFILTER_TXT, enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))
        
    elif query.data == "globalfilter":
        buttons = [[
            InlineKeyboardButton('🔮𝘉𝘶𝘵𝘵𝘰𝘯𝘍𝘰𝘳𝘮𝘢𝘵🔮', 'buttong')
            ],[
            InlineKeyboardButton('🔮𝘊𝘭𝘰𝘴𝘦🔮', 'close_data'),
            InlineKeyboardButton('🔮𝘉𝘢𝘤𝘬🔮', 'openfilter')           
        ]]
        if query.from_user.id not in ADMINS:
            return await query.answer("𝘠𝘰𝘶 𝘈𝘳𝘦 𝘕𝘰𝘵 𝘈𝘶𝘵𝘩𝘰𝘳𝘪𝘻𝘦𝘥 𝘛𝘰 𝘗𝘦𝘳𝘧𝘰𝘮 𝘛𝘩𝘪𝘴 𝘈𝘤𝘵𝘪𝘰𝘯", show_alert=True)
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.GLOBALFILTER_TXT, enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))
        
    elif query.data.startswith("button"):
        buttons = [[
            InlineKeyboardButton('🔮𝘊𝘭𝘰ꜱ𝘦🔮', 'close_data'),
            InlineKeyboardButton('🔮𝘉𝘢𝘤𝘬🔮', f"{'manuelfilter' if query.data == 'button' else 'globalfilter'}")           
        ]]
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.BUTTON_TXT, enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))
   
    elif query.data == "coct":
        buttons = [[
            InlineKeyboardButton('🔮𝘊𝘭𝘰𝘴𝘦🔮', 'close_data'),
            InlineKeyboardButton('🔮𝘉𝘢𝘤𝘬🔮', 'help')           
        ]]
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.CONNECTION_TXT, enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))
         
    elif query.data == "newdata":
        buttons = [[
            InlineKeyboardButton('🔮𝘊𝘭𝘰𝘴𝘦🔮', 'close_data'),
            InlineKeyboardButton('🔮𝘉𝘢𝘤𝘬🔮', 'help')           
        ]]
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.FILE_TXT, enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))
        
    elif query.data == "extmod":
        buttons = [[
            InlineKeyboardButton('🔮𝘊𝘭𝘰𝘴𝘦🔮', 'close_data'),
            InlineKeyboardButton('🔮𝘉𝘢𝘤𝘬🔮', 'help')           
        ]]
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.EXTRAMOD_TXT, enums.ParseMode.HTML),             reply_markup=InlineKeyboardMarkup(buttons))
        
    elif query.data == "gpmanager":
        buttons = [[
            InlineKeyboardButton('🔮𝘊𝘭𝘰𝘴𝘦🔮', 'close_data'),
            InlineKeyboardButton('🔮𝘉𝘢𝘤𝘬🔮', 'help')           
        ]]
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.GROUPMANAGER_TXT, enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))           
        
    elif query.data == "stats":
        buttons = [[
            InlineKeyboardButton('🔮𝘙𝘦𝘍𝘳𝘦𝘴𝘩🔮', 'stats'),
            InlineKeyboardButton('🔮𝘉𝘢𝘤𝘬🔮', 'help')           
        ]]
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit('𝘓𝘰𝘢𝘥𝘪𝘯𝘨....')
        await query.edit_message_media(InputMediaPhoto(random.choice(PICS), script.STATUS_TXT.format(total, users, chats, monsize, free), enums.ParseMode.HTML), reply_markup=InlineKeyboardMarkup(buttons))
    
    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        grpid = await active_connection(str(query.from_user.id))
        if str(grp_id) != str(grpid):
            return await query.message.edit("𝘔𝘢𝘴𝘵𝘦𝘳 𝘈𝘤𝘵𝘪𝘷𝘦 𝘊𝘰𝘯𝘯𝘦𝘤𝘵𝘪𝘰𝘯 𝘏𝘢𝘴 𝘉𝘦𝘦𝘯 𝘊𝘩𝘢𝘯𝘨𝘦𝘥. 𝘎𝘰 𝘛𝘰 ／𝘚𝘦𝘵𝘵𝘪𝘯𝘨𝘴")
        if status == "True": await save_group_settings(grpid, set_type, False)
        else: await save_group_settings(grpid, set_type, True)
        settings = await get_settings(grpid)
        if settings is not None:
            buttons = [[
                InlineKeyboardButton(f"𝘍𝘪𝘭𝘵𝘦𝘳 𝘉𝘶𝘵𝘵𝘰𝘯 : {'sɪɴɢʟᴇ' if settings['button'] else 'ᴅᴏᴜʙʟᴇ'}", f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],[
                InlineKeyboardButton(f"𝘉𝘖𝘛𝘱𝘮: {'ᴏɴ' if settings['botpm'] else 'ᴏꜰꜰ'}", f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
                ],[                
                InlineKeyboardButton(f"𝘙𝘦𝘴𝘵𝘳𝘪𝘤𝘵𝘊𝘰𝘯𝘵𝘦𝘯𝘵 : {'ᴏɴ' if settings['file_secure'] else 'ᴏꜰꜰ'}", f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],[
                InlineKeyboardButton(f"𝘐𝘔𝘋𝘉 : {'ᴏɴ' if settings['imdb'] else 'ᴏꜰꜰ'}", f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],[
                InlineKeyboardButton(f"𝘚𝘱𝘦𝘭𝘭𝘪𝘯𝘨 : {'ᴏɴ' if settings['spell_check'] else 'ᴏꜰꜰ'}", f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],[
                InlineKeyboardButton(f"𝘞𝘦𝘭𝘤𝘰𝘮𝘦 𝘛𝘦𝘹𝘵 : {'ᴏɴ' if settings['welcome'] else 'ᴏꜰꜰ'}", f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
            ]]
            await query.message.edit_reply_markup(InlineKeyboardMarkup(buttons))







