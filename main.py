import requests
import time
from bs4 import BeautifulSoup
from telebot import TeleBot
import threading
import datetime
from secrets import TELEGRAM_TOKEN
import os
import datetime
import shutil
import json

app = TeleBot(TELEGRAM_TOKEN)
URLS = {
	'first': 'http://api.encar.com/search/car/list/premium?count=true&q=(And.(And.Hidden.N._.CarType.Y._.Year.range(201200..)._.Price.range(..900).)_.AdType.B.)&sr=%7CModifiedDate%7C0%7C8',
	'second': 'http://api.encar.com/search/car/list/premium?count=true&q=(And.Hidden.N._.CarType.Y._.Year.range(201200..)._.Price.range(..900).)&sr=%7CModifiedDate%7C0%7C20'
}


@app.message_handler(commands=['start'])
def example_command(message):
	geted_id = message.chat.id
	with open('telegram.txt', 'r', encoding='utf-8') as f:
		ids_list = f.read().split(',')
		ids = ids_list
	if str(geted_id) not in ids:
		ids.append(str(geted_id))
		# print(message)
		with open('telegram.txt', 'a') as f:
			f.write(f'{str(geted_id)},')
	msg = '''
	Здравствуйте!\nТеперь вам будут присылаться новые объявления из сайта otomoto.pl\n
	Чтоб отказатья от подписки, введите /stop
	'''
	app.send_message(geted_id, msg)

@app.message_handler(commands=['stop'])
def example_command(message):
	geted_id = message.chat.id
	with open('telegram.txt', 'r', encoding='utf-8') as f:
		ids_list = f.read().split(',')
	msg = '''
		ID пользователя не найдено, кажется что Вы ещё не подписаны на рассылку.Подписаться - /start
	'''
	if str(geted_id) in ids_list:
		ids_list.remove(str(geted_id))
		updated_ids_list = ','.join(str(x) for x in ids_list)
		with open('telegram.txt', 'w') as f:
			f.write(updated_ids_list)
		msg = '''
			Вам больше не будут рприходить сообщения от меня.\nЧто бы получать уведомления снова, введите команду /start
		'''
	app.send_message(geted_id, msg)

def send_zip(zip_name):
	with open('telegram.txt', 'r') as f:
		ids_list = f.read().split(',')
		for chat_id in ids_list:
			try:
				app.send_document(chat_id, open(zip_name+'.zip','rb'))
			except:
				pass

def bot_thread():
	print('### START TELEGRAM ###')
	app.polling()

def encar_parser(response):
	keys = list(response.keys())
	values = list(response.values())
	car_id = response["Id"]
	text = f'http://www.encar.com/dc/dc_cardetailview.do?carid={car_id}\n'
	for i in range(len(keys)):
		if keys[i] == 'Photo' or keys[i] == 'Photos':
			continue
		text += f'{keys[i]}: {values[i]}\n'
	car_id = f'encar - {car_id}'
	try:
		os.mkdir(car_id)
	except:
		shutil.rmtree(f'{car_id}/')
		os.mkdir(car_id)
	with open(f'./{car_id}/'+car_id+'.txt', 'w') as f:
		f.write(text)
	image_id = 0
	for slide in response['Photos']:
		image = requests.get(f"http://ci.encar.com/carpicture{slide['location']}").content
		with open(f'./{car_id}/'+str(car_id)+' --- '+str(image_id)+'.jpg', 'wb') as f:
			f.write(image)
		image_id += 1
	shutil.make_archive(car_id, 'zip', car_id)
	shutil.rmtree(f'{car_id}/')
	send_zip(car_id)
	os.remove(car_id+'.zip')

def parser_thread():
	print('### START PARSER ###')
	old_encar_first = ''
	old_encar_second = ''
	while True:
		try:
			response_first = json.loads(requests.get(URLS['first']).text)['SearchResults'][0]
			response_second = json.loads(requests.get(URLS['second']).text)['SearchResults'][0]
		except Exception as e:
			print(e)
			print('Exception in encar global requests')
			continue
		new_encar_first = response_first['Manufacturer'] + response_first['Model'] + response_first['Badge']
		new_encar_second = response_second['Manufacturer'] + response_second['Model'] + response_second['Badge']
		if old_encar_first != new_encar_first:
			encar_parser(response_first)
			old_encar_first = new_encar_first
			print('checkout ------- encar 1 ------- ' + datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
		if old_encar_second != new_encar_second:
			encar_parser(response_second)
			old_encar_second = new_encar_second
			print('checkout ------- encar 2 ------- ' + datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
		time.sleep(300)

if __name__ == '__main__':
	thr_bot = threading.Thread(target=bot_thread)
	thr_bot.start()
	thr_parser = threading.Thread(target=parser_thread)
	thr_parser.start()