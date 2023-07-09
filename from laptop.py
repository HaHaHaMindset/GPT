import discord
import os
from discord.ext import commands
import time
import asyncio
import selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from bs4 import BeautifulSoup
import csv
from selenium.webdriver.common.by import By
from keyboard import press
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import MoveTargetOutOfBoundsException
from selenium.common.exceptions import ElementNotInteractableException
import urllib
from csv import writer
import pandas
import pandas as pd
from selenium.webdriver.common.action_chains import ActionChains
from discord import Webhook
from discord_webhook import DiscordWebhook, DiscordEmbed
from selenium.webdriver.firefox.options import Options
import threading
from threading import Thread
import concurrent.futures
import requests
import tracemalloc
from collections import defaultdict
info_enabled = {}


user_check_counters = defaultdict(int)
tracemalloc.start()

intents = discord.Intents.all()

client = commands.Bot(command_prefix='!', intents=intents)
global stop_flag
# Define some global variables
stopper = False
stop_flag = False
max_price = None
email = None
password = None
Title = None
Price = None
row = None
#updates = []
# Define some global variables
running_clients = {}
phone_numbers = {}
global info
info = {}
stop_flags = {}
stoppers = {}
custom_message1 = False
custom_messages = {}
user_updates = {}
updates = {}  # define updates as a dictionary
user_id = ""

last_start_times = {}
# Load client settings from CSV file
client_settings = {}
# Load client settings from the CSV file
with open('client_settings.csv', 'r', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        user_id = row['user_id']
        client_settings[user_id] = {
            'email': row['email'],
            'password': row['password'],
            'max_price': int(row['max_price']),
            'location': row['location'],
            'range_couch': int(row['range_couch']),
        }


def check_credentials(email, password):
    # Set up headless browser with necessary options
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Firefox(options=options)

    # Navigate to the login page and fill in email and password
    driver.get('https://www.facebook.com/messages')
    driver.find_element(By.NAME, 'email').send_keys(email)
    driver.find_element(By.NAME,'pass').send_keys(password)

    # Submit the login form and wait for page to load
    driver.find_element(By.NAME, 'login').click()
    time.sleep(5)

    # Check if login was successful
    if 'www.facebook.com/messages' in driver.current_url:
        driver.quit()
        return True
    else:
        print(driver.page_source)  # Print out the page source for debugging
        driver.quit()
        return False


@client.command()
async def restart(ctx):
    global running_clients
    if str(ctx.author.id) in running_clients:
        running_clients[str(ctx.author.id)]['restart_flag'] = True
        await ctx.send('Restarting the setup process...')

# List of admin user IDs or role IDs
admin_ids = ["1022636400274845777", "248935198459166722"]

def is_admin(user):
    return any(role.id in admin_ids for role in user.roles) or str(user.id) in admin_ids

@client.command()
async def admin_start(ctx, user_id: int):
    print(client_settings)
    # Check if the author is an admin
    if not is_admin(ctx.author):
        await ctx.send("You don't have permission to use this command.")
        return

    # Get the specified user's settings
    if str(user_id) in client_settings:
        email = client_settings[str(user_id)]['email']
        password = client_settings[str(user_id)]['password']
        max_price = int(client_settings[str(user_id)]['max_price'])
        location = client_settings[str(user_id)]['location']
        range_couch = client_settings[str(user_id)]['range_couch']
    else:
        await ctx.send(f"No settings found for user ID {user_id}.")
        return

    # Start the flipper task for the specified user
    stop_flag = False
    user = await client.fetch_user(user_id)

    async def run_flipper(ctx, email, password, max_price, location, range_couch):
        await flipper(ctx, email, password, max_price, stop_flag, str(user_id), location, range_couch)

    async def start_flipper_thread(ctx, email, password, max_price, location, range_couch):
        task = asyncio.create_task(run_flipper(ctx, email, password, max_price, location, range_couch))
        running_clients[str(user_id)] = {'task': task}
        await ctx.send(f'Starting the flipper for user {user.name}')

        # Wait for the flipper task to complete or be cancelled
        try:
            await task
        except asyncio.CancelledError:
            pass

    asyncio.create_task(start_flipper_thread(ctx, email, password, max_price, location, range_couch))


@client.command()
async def start(ctx):
    if ctx.channel.name != "general" and ctx.channel.name != "suggestions":
        global running_clients
        
        global last_start_times

        client_id = str(ctx.author.id)

        # Check if the user has called the command within the last 5 minutes
        last_start_time = last_start_times.get(client_id, 0)
        current_time = time.time()
        if current_time - last_start_time < 300:
            await ctx.send("!start has already been called. Please finish the setup before calling it again.")
            return

        last_start_times[client_id] = current_time
        
        # Check if the client has already started the flipper task
        if str(ctx.author.id) in running_clients:
            # Stop the existing flipper task
            running_clients[str(ctx.author.id)]['stop_flag'] = True
            del running_clients[str(ctx.author.id)]
            await ctx.send('Stopping the flipper for this client')
        
        # Add this dictionary to keep track of users in the authentication process
        authentication_in_progress = {}
        
        # Load client settings from CSV if they exist, otherwise prompt for new settings
        client_id = str(ctx.author.id)
        if client_id in client_settings:
            email = client_settings[client_id]['email']
            password = client_settings[client_id]['password']
            max_price = int(client_settings[client_id]['max_price'])
            location = client_settings[client_id]['location']
            range_couch = client_settings[client_id]['range_couch']

        else:
            while True:
                if ctx.author.id not in authentication_in_progress or not authentication_in_progress[ctx.author.id]:
                    await ctx.send('Please enter your Facebook email / phone number: (This will be immediately deleted)')
                    email_message = await client.wait_for('message', check=lambda message: message.author == ctx.author and not message.content.startswith('!'))
                    email = email_message.content
                    await email_message.delete()

                    await ctx.send('Please enter your Facebook password: (This will be immediately deleted)')
                    password_message = await client.wait_for('message', check=lambda message: message.author == ctx.author and not message.content.startswith('!'))
                    password = password_message.content

                    await ctx.send('Authenticating your credentials... one moment (You may have to allow access from our server on your Facebook account)')
                    await password_message.delete()

                    # Set the flag for the user to indicate they are in the authentication process
                    authentication_in_progress[ctx.author.id] = True

                    if check_credentials(email, password):
                        # Reset the flag if the authentication is successful
                        authentication_in_progress[ctx.author.id] = False
                        break

                    if user_id in running_clients and running_clients[user_id]['restart_flag']:
                        authentication_in_progress[ctx.author.id] = False
                        return await start(ctx)

                    await ctx.send('Invalid email or password. Please try again.')
                    # Reset the flag if the authentication fails
                    authentication_in_progress[ctx.author.id] = False
            
        
           # Prompt the user for the location
           # Prompt the user for the location
            pattern = r'^[A-Za-z]+(?:\s[A-Za-z]+)?,\s[A-Za-z]+(?:\s[A-Za-z]+)?$'

            await ctx.send('Please enter the location in this format: City, State:')

            while True:
                location_input = await client.wait_for('message', check=lambda message: message.author == ctx.author and not message.content.startswith('!'))
                location_str = location_input.content.strip()

                # Updated pattern
                pattern = r'^[A-Za-z]+(?:\s[A-Za-z]+)?,\s[A-Za-z]+(?:\s[A-Za-z]+)?$'

                if not re.match(pattern, location_str):
                    await ctx.send('Please enter the location in this format: City, State:')
                else:
                    location = location_str
                    break
            
            # Prompt the user for the max price
            pattern = r'^\d{1,4}$'

            await ctx.send('Please enter the max price (up to 4 digits, no commas or dollar signs):')

            while True:
                max_price_input = await client.wait_for('message', check=lambda message: message.author == ctx.author and not message.content.startswith('!'))
                max_price_str = max_price_input.content.strip()

                if not re.match(pattern, max_price_str):
                    await ctx.send('Numbers Only - Try Again!')
                else:
                    max_price = int(max_price_str)
                    break
                
            # Prompt the user for the range price
            #pattern = r'^\d{1,3}$'
            
            await ctx.send('Please enter the corresponding letter to search for a distance: \n a for 1 mile\n b for 2 miles\n c for 5 miles\n d for 10 miles\n e for 20 miles\n f for 40 miles\n')

            while True:
                range_input = await client.wait_for('message', check=lambda message: message.author == ctx.author and not message.content.startswith('!'))
                range_str = range_input.content.strip().lower()

                if range_str == 'a':
                    range_couch = 1
                    break
                elif range_str == 'b':
                    range_couch = 2
                    break
                elif range_str == 'c':
                    range_couch = 5
                    break
                elif range_str == 'd':
                    range_couch = 10
                    break
                elif range_str == 'e':
                    range_couch = 20
                    break
                elif range_str == 'f':
                    range_couch = 40
                    break
                elif range_str == 'g':
                    range_couch = 60
                    break
                elif range_str == 'h':
                    range_couch = 80
                    break
                elif range_str == 'i':
                    range_couch = 100
                    break
                else:
                    await ctx.send('Invalid input - Try Again!')

            # Save the client settings to the client_settings dictionary and CSV file
            client_settings[client_id] = {
                'email': email,
                'password': password,
                'max_price': max_price,
                'location': location,
                'range_couch': range_couch,
            }

            with open('client_settings.csv', 'w', newline='') as csvfile:
                fieldnames = ['user_id', 'email', 'password', 'max_price', 'location', 'range_couch']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for user_id, settings in client_settings.items():
                    writer.writerow({'user_id': user_id, 'email': settings['email'], 'password': settings['password'], 'max_price': settings['max_price'], 'location': settings['location'], 'range_couch': settings['range_couch']})
        
        # Check if the user has waited at least 5 minutes since the last start command
        #last_start_time = last_start_times.get(client_id, 0)
        #current_time = time.time()
        #if current_time - last_start_time < 300:
        #    time_left = int(300 - (current_time - last_start_time))
        #    await ctx.send(f"You can only start the flipper once every 5 minutes. Please wait {time_left} seconds before trying again.")
        #    return
        #last_start_times[client_id] = current_time
        
        # Start the flipper task
        stop_flag = False
        
        async def run_flipper(ctx, email, password, max_price, location, range_couch):
            await flipper(ctx,email,password,max_price,stop_flag,client_id, location, range_couch)

        async def start_flipper_thread(ctx, email, password, max_price, location, range_couch):
            task = asyncio.create_task(run_flipper(ctx, email, password, max_price, location, range_couch))
            running_clients[client_id] = {'task': task}
            await ctx.send(f'Starting the flipper for user {ctx.author.name}')

            # Wait for the flipper task to complete or be cancelled
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Use create_task() instead of run()
        asyncio.create_task(start_flipper_thread(ctx, email, password, max_price, location, range_couch))



async def flipper(ctx, email, password, max_price, stop_flag, user_id, location, range_couch):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Run the blocking code in a separate thread
        result = await client.loop.run_in_executor(executor, flipper_blocking, ctx, email, password, max_price, user_id, location, range_couch)
        
        
def flipper_blocking(ctx, email, password, max_price, user_id, location, range_couch):
    stop_flag
    channel_id = ctx.channel.id
    print(channel_id)
    while True:
        options = Options()
        options.set_preference('geo.enabled', True)
        options.set_preference('geo.provider.use_corelocation', True)
        options.set_preference('geo.prompt.testing', True)
        options.set_preference('geo.prompt.testing.allow', True)
        options.add_argument('--headless')
        driver = webdriver.Firefox()
        driver.get("https://www.facebook.com/marketplace/")
        time.sleep(5)

        #finds the email and password fields and enters in my credentials
        email_input = driver.find_element(By.NAME, "email")
        password_input = driver.find_element(By.NAME, "pass")
        email_input.send_keys(email)
        password_input.send_keys(password)
        time.sleep(3)
        #finds the login button and clicks it

        
        if driver.current_url == "https://www.facebook.com/marketplace/":
            login_attempt = driver.find_element(By.XPATH, '//div[@class="x1i10hfl x1qjc9v5 xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli x1n2onr6 x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x3nfvp2 x1q0g3np x87ps6o x1lku1pv x1a2a7pz xtvsq51 xhk9q7s x1otrzb0 x1i1ezom x1o6z2jb x1vqgdyp x6ikm8r x10wlt62 xexx8yu xn6708d x1120s5i x1ye3gou"][@aria-label="Accessible login button"]')
            hover = ActionChains(driver).move_to_element(login_attempt)
            hover.perform()
            login_attempt.click()
        else:
            login_attempt = driver.find_element(By.XPATH, '//button[@class="_42ft _4jy0 _52e0 _4jy6 _4jy1 selected _51sy"][@name="login"]')
            hover = ActionChains(driver).move_to_element(login_attempt)
            hover.perform()
            login_attempt.click()
        time.sleep(10)

        location_1 = driver.find_element(By.XPATH, '//span[@class = "x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x xudqn12 x3x7a5m x6prxxf xvq8zen x1s688f x1qq9wsj"]')
        time.sleep(1)
        location_1.click()
        time.sleep(1)
        
            

        
        actual_location = driver.find_element(By.XPATH, '//input[@class = "x1i10hfl xggy1nq x1s07b3s x1kdt53j x1a2a7pz xjbqb8w x76ihet xwmqs3e x112ta8 xxxdfa6 x9f619 xzsf02u x1uxerd5 x1fcty0u x132q4wb x1a8lsjc x1pi30zi x1swvt13 x9desvi xh8yej3 x15h3p50 x10emqs4"]')
        time.sleep(3)
        actual_location.click()
        time.sleep(3)
        actual_location.send_keys(location)
        time.sleep(3)
        actual_location.send_keys(Keys.ARROW_DOWN)
        time.sleep(3)
        actual_location.send_keys(Keys.RETURN)

        time.sleep(3)
        #apply_location = driver.find_element(By.XPATH, '//div[@class = "x1i10hfl xjbqb8w x6umtig x1b1mbwd xaqea5y xav7gou x1ypdohk xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x87ps6o x1lku1pv x1a2a7pz x9f619 x3nfvp2 xdt5ytf xl56j7k x1n2onr6 xh8yej3"]')
        time.sleep(3)
        #wait = WebDriverWait(driver, 10)
        #wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class = "x1i10hfl xjbqb8w x6umtig x1b1mbwd xaqea5y xav7gou x1ypdohk xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x87ps6o x1lku1pv x1a2a7pz x9f619 x3nfvp2 xdt5ytf xl56j7k x1n2onr6 xh8yej3"]')))
        count = 0
        while count < 5:
            try:
                apply_location = driver.find_elements(By.XPATH, '//div[@class="x1i10hfl xjbqb8w x6umtig x1b1mbwd xaqea5y xav7gou x1ypdohk xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x87ps6o x1lku1pv x1a2a7pz x9f619 x3nfvp2 xdt5ytf xl56j7k x1n2onr6 xh8yej3"]')
                if apply_location:
                    apply_location[-1].click()
                    time.sleep(5)
                    count += 1
                else:
                    print('No apply_location buttons found')
                    break
            except (NoSuchElementException, ElementNotInteractableException) as h:
                print('Error: apply_location button not found')
                break
        #apply_location_1 = driver.find_element(By.XPATH, '//div[@class = "x1i10hfl xjbqb8w x6umtig x1b1mbwd xaqea5y xav7gou x1ypdohk xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x87ps6o x1lku1pv x1a2a7pz x9f619 x3nfvp2 xdt5ytf xl56j7k x1n2onr6 xh8yej3"]')
        time.sleep(7)

        
        #finds the search bar and enters in what I am searching for
        search = driver.find_element(By.XPATH, '//input[@class = "x1i10hfl xggy1nq x1s07b3s x1kdt53j x1yc453h xhb22t3 xb5gni xcj1dhv x2s2ed0 xq33zhf xjyslct xjbqb8w x6umtig x1b1mbwd xaqea5y xav7gou xnwf7zb x40j3uw x1s7lred x15gyhx8 x9f619 xzsf02u xdl72j9 x1iyjqo2 xs83m0k xjb2p0i x6prxxf xeuugli x1a2a7pz x1n2onr6 x15h3p50 xm7lytj xsyo7zv xdvlbce x16hj40l xc9qbxq xo6swyp x1ad04t7 x1glnyev x1ix68h3 x19gujb8"]')
        search.send_keys("sectional")
        search.send_keys(Keys.RETURN)
        time.sleep(10)
        
        
        changing_the_range = driver.find_element(By.XPATH, '//div[@class = "x1i10hfl x1qjc9v5 xjbqb8w xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xdl72j9 x2lah0s xe8uvvx x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x1q0g3np x87ps6o x1lku1pv x78zum5 x1a2a7pz x1xmf6yo"]')
        changing_the_range.click()
        time.sleep(5)
        try:
            range_input_box = driver.find_element(By.XPATH, '//label[@class = "xjhjgkd x1epquy7 xsnmfus x1562eck xcymrrh x1268tai x1mxuytg x14hpm34 xqvykr2 x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x178xt8z xm81vs4 xso031l xy80clv x78zum5 xdt5ytf x6ikm8r x10wlt62 x1n2onr6 x1ja2u2z x1egnk41 x1ypdohk x1a2a7pz"]')
        except NoSuchElementException:
            range_input_box = driver.find_element(By.XPATH, '//div[@class = "xjyslct xjbqb8w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x78zum5 x1jchvi3 x1fcty0u x132q4wb xdj266r x11i5rnm xat24cr x1mh8g0r x1a2a7pz x1pi30zi x1n2onr6 x16tdsg8 xh8yej3 x1ja2u2z xzsf02u x9desvi x1a8lsjc x1swvt13"]')
        range_input_box.click()
        time.sleep(3)
        list_of_couch_ranges = driver.find_elements(By.XPATH, '//div[@class = "x1i10hfl xjbqb8w x6umtig x1b1mbwd xaqea5y xav7gou xe8uvvx x1hl2dhg xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x87ps6o x1lku1pv x1a2a7pz x6s0dn4 xjyslct x9f619 x1ypdohk x78zum5 x1q0g3np x2lah0s xnqzcj9 x1gh759c xdj266r xat24cr x1344otq x1de53dj xz9dl7a xsag5q8 x1n2onr6 x16tdsg8 x1ja2u2z"]')
        time.sleep(3)
        if range_couch == 1:
            list_of_couch_ranges[0].click()
        elif range_couch == 2:
            list_of_couch_ranges[1].click()
        elif range_couch == 5:
            list_of_couch_ranges[2].click()
        elif range_couch == 10:
            list_of_couch_ranges[3].click()
        elif range_couch == 20:
            list_of_couch_ranges[4].click()
        elif range_couch == 40:
            list_of_couch_ranges[5].click()
        elif range_couch == 60:
            list_of_couch_ranges[6].click()
        elif range_couch == 80:
            list_of_couch_ranges[7].click()
        else:
            list_of_couch_ranges[8].click()
        time.sleep(3)
        count2 = 0
        while count2 < 5:
            try:
                apply_location = driver.find_elements(By.XPATH, '//div[@class="x1i10hfl xjbqb8w x6umtig x1b1mbwd xaqea5y xav7gou x1ypdohk xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x87ps6o x1lku1pv x1a2a7pz x9f619 x3nfvp2 xdt5ytf xl56j7k x1n2onr6 xh8yej3"]')
                if apply_location:
                    apply_location[-1].click()
                    time.sleep(5)
                    count += 1
                else:
                    print('No apply_location buttons found')
                    break
            except (MoveTargetOutOfBoundsException, ElementNotInteractableException, NoSuchElementException) as e:
                print('Error: apply_location button not found')
                break
        
        max_price_input = driver.find_element(By.XPATH, '//input[@class="x1i10hfl xggy1nq x1s07b3s x1kdt53j x1a2a7pz xmjcpbm x1n2xptk xkbpzyx xdppsyt x1rr5fae xhk9q7s x1otrzb0 x1i1ezom x1o6z2jb x9f619 xzsf02u x1qlqyl8 xk50ysn x1y1aw1k xn6708d xwib8y2 x1ye3gou xh8yej3 xha3pab xyc4ar7 x10lcxz4 xzt8jt4 xiighnt xviufn9 x1b3pals x10bruuh x1yc453h xc9qbxq"][@placeholder="Max"]')
        max_price_input.send_keys(max_price)
        max_price_input.send_keys(Keys.RETURN)
        #finds the search button and clicks it
        #search_attempt = driver.find_element(By.XPATH, "//button[@type='submit']")
        #search_attempt.click()
        #time.sleep(10)


        #initializes an empty list to store all the links in
        links = []

        #goes through each page of the search and appends all the links to the list
        for i in range(5):
            soup=BeautifulSoup(driver.page_source, 'html.parser')
            for a in soup.findAll('a', attrs={'href': re.compile("marketplace/item/")}):
                links.append(a['href'][0:36])
            #driver.find_element(By.CLASS_NAME, '_1glk').click()
            time.sleep(3)

        #removes duplicates from the list of links
        links = list(dict.fromkeys(links))
        #print(*links,sep='\n')
        #opens a new csv file to store the data in
        del links[0]
        links = (['https://www.facebook.com{0}'.format(i) for i in links])
        #print(links)
        #y = []
        #print(*links,sep='\n')
        #print(*y, sep='\n')
        #print(links)
        #for link in links:
        #cols = ["Links"]
        filename = f"{user_id}_shows.csv"
        if not os.path.isfile(filename):
            pd.DataFrame(columns=['email']).to_csv(filename, index=False)
        
        # Read the existing shows for the user from user_id_shows.csv
        df = pd.read_csv(filename)
        existing_shows = set(df['email'].tolist())

        # Get the new shows that match the criteria
        filtered_links = []
        for link in links:
            if link not in existing_shows:
                filtered_links.append(link)
        print(filtered_links)

        # Add the new shows to user_id_shows.csv
        df = pd.concat((df, pd.DataFrame(columns=['email'], data=[l for l in links if l not in df['email'].values])))
        df.to_csv(filename, index=False)
        #print(links)
        if filtered_links == []:
            pass
        else:
            webhook = DiscordWebhook(url='https://discord.com/api/webhooks/1043795569488973825/iVExWkmO8OLQliXrN4aayJX5MkA_L5J3hza31PLSB-WeUNRZsFCciWaQFiPww0ZPmE43', content= str(filtered_links))
            response = webhook.execute()

        with open('sectional_data.csv', 'a') as file:
            writer = csv.writer(file)
            headers = ["Title","Price","Image"]
            writer.writerow(headers)


        #goes to each link in the list and grabs the title, price, and image
        for link in filtered_links:
            driver.get(link)
            time.sleep(7)
            try:
                listing_time = driver.find_element(By.XPATH, '//span[@class = "x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x4zkp8e x676frb x1nxh6w3 x1sibtaa xo1l8bm xi81zsa"][@dir = "auto"]')
            except NoSuchElementException:
                continue
            if ("minutes" not in listing_time.text) or ("minute" not in listing_time.text):
                continue
            title_element = driver.find_elements(By.TAG_NAME, "h1")
            price_element = driver.find_elements(By.XPATH, '//span[@class = "x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x xudqn12 x676frb x1lkfr7t x1lbecb7 xk50ysn xzsf02u"][@dir="auto"]')
            title_object = title_element[0]
            price_object = price_element[0]
            title = title_object.text
            price = price_object.text
            price = price[1:]
            price = price.split('$')[0]

            # Remove commas from price string
            price = price.replace(',', '')

            # Extract the integer up to the first non-integer character
            int_price = ''
            for char in price:
                if char.isdigit():
                    int_price += char
                else:
                    break

            if int(int_price) > max_price:
                continue
            price = int_price
            #title = title_element.text 
            #price = price_element.text
            #image = driver.find_element(By.CLASS_NAME, "_46-i")
            image = driver.find_element(By.TAG_NAME, 'img').get_attribute('src')
            time.sleep(5)
            row = [x for x in title] + [y for y in price] + [link] 
            with open('sectional_data.csv', 'a', encoding = 'utf-8') as file: 
                writer = csv.writer(file) 
                writer.writerow(row) 
            message = driver.find_element(By.XPATH, ('//span[@class = "x1lliihq x6ikm8r x10wlt62 x1n2onr6 xlyipyv xuxw1ft"][contains(text(),"Message")]'))
            hover = ActionChains(driver).move_to_element(message)
            hover.perform()
            message.click()
            #sendy = (By.XPATH, ('/html/body/div[1]/div[1]/div[1]/div/div[5]/div/div/div[3]/div[2]/div/div[2]/div/div[2]/div/div[2]/div[1]/div[1]/div[3]/div/div[1]/div/div'))
            #sendy.click()
            #message.click()
            #message = WebDriverWait(driver, 1000000).until(EC.element_to_be_clickable((By.XPATH, ('//span[contains(text(),"Message")]'))))
            #send message
            #message_box = driver.find_element(By.XPATH, '//span[contains(text(),"Please type your message to the seller")]')
            #if message:
            #message[0].click()
            #message.click()
            time.sleep(2) 
            #send message
            try:
                message_box = driver.find_element(By.XPATH, '//textarea[@aria-invalid="false"][@class="x1i10hfl xggy1nq x1s07b3s xjbqb8w x76ihet xwmqs3e x112ta8 xxxdfa6 x9f619 xzsf02u x78zum5 x1jchvi3 x1fcty0u x132q4wb xyorhqc xaqh0s9 x1a2a7pz x6ikm8r x10wlt62 x1pi30zi x1swvt13 xtt52l0 xh8yej3"]')
            except MoveTargetOutOfBoundsException:
                continue
            #message_box = driver.find_element(By.XPATH, "//label[@aria-label='Please type your message to the seller']")
            time.sleep(2) 
            hover = ActionChains(driver).move_to_element(message_box)
            hover.perform()
            # The rest of the code that uses custom_message
            print(custom_messages)
            if ctx.author.id in custom_messages:
                message123 = custom_messages[ctx.author.id]
            else:
                message123 = "Hey, is this still available?"
            
            message_box.click()
            actions = ActionChains(driver)
            actions.move_to_element(message_box)
            actions.send_keys_to_element(message_box, message123)
            actions.perform()
            message_box_send = driver.find_element(By.XPATH, '//div[@class="x1i10hfl xjbqb8w x6umtig x1b1mbwd xaqea5y xav7gou x1ypdohk xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x87ps6o x1lku1pv x1a2a7pz x9f619 x3nfvp2 xdt5ytf xl56j7k x1n2onr6 xh8yej3"][@aria-label="Send Message"]')
            hover = ActionChains(driver).move_to_element(message_box_send)
            hover.perform()
            message_box_send.click()
            #webhook = DiscordWebhook(url='https://discord.com/api/webhooks/1075225501326647296/O77JuLLBFiIlROJgsRZje8TmWGLYy65TLPURjl4uqlUyr38EDdZHF6r4-xbKUBjkKdPm', content=f"price: {price}\ntitle: {title}")
            #response = webhook.execute()
            if user_id not in updates:
                updates[user_id] = []
            updates[user_id].append((price, title, link))
            print(updates)
            #couch_data(ctx, title, price, row)
            
            if user_id in phone_numbers:
                # Code to send text notification goes here
                pass
            
            time.sleep(15)
            #row = [x.text for x in title] + [y.text for y in price] + [image] 
            #with open('sectional_data.csv', 'a', encoding = 'utf-8') as file: 
            #    writer = csv.writer(file) 
            #    writer.writerow(row) 


        #closes the browser        
        driver.quit()   
        time.sleep(180)
        print(stop_flag)
        user_id = str(ctx.author.id)
        if user_id in stoppers and stoppers[user_id]:
            break

#def couch_data(ctx, title, price, row):
#    with concurrent.futures.ThreadPoolExecutor() as executor:
#        executor.submit(asyncio.run, couch_data_send(ctx, title, price, row))

#async def couch_data_send(ctx, title, price, row):
#    await ctx.send(f"New couch found: {row}")
@client.command()
async def all_couches(ctx, *args):
    global couch_dump
    if len(args) == 0:
        await ctx.send("Please do !all_couches true or false to enable all couches without filtering")
    elif args[0] == "true":
        couch_dump = True
        await ctx.send("All couches will now be displayed.")
    else:
        await ctx.send("Turning off couch dump")
        couch_dump = False

async def couch_dump(ctx, title, price, row):
    if couch_dump:
        await ctx.send(f"New couch found: {row}")
 
async def create_paypal_sub():
    #create a paypal subscriotion for $50 per month with a 3 day free trial
    
async def couch_data(ctx, title, price, row):
    global updates, user_channels, info_enabled, user_check_counters
    if len(updates) > 0:
        for user_id in updates:
            if user_id in user_channels:
                channel_id = user_channels[user_id]
                channel = client.get_channel(channel_id)
                if channel is not None:
                    for update in updates[user_id]:
                        await channel.send(f"New couch found: {update}")
                        await couch_dump(ctx, title, price, row)
            if user_id in info_enabled and info_enabled[user_id]:
                if user_id in user_check_counters:
                    user_check_counters[user_id] += 1
                else:
                    user_check_counters[user_id] = 1
                if user_check_counters[user_id] % 10 == 0:
                    await ctx.send(f"Hi {ctx.author.name}, I'm still running in the background and checking for couches! If you want to stop the bot, please type !stop")
                    

@client.command()
async def custom(ctx, *args):
    global custom_messages
    if len(args) == 0:
        await ctx.send("Please type your custom message after !custom")
    else:
        custom_message = " ".join(args)
        custom_messages[ctx.author.id] = custom_message
        await ctx.send("Your message is now custom! " + custom_message)
        

# Create a dictionary to store user IDs and their respective channel IDs
user_channels = {}


@client.command()
async def info(ctx, *args):
    global info_enabled, user_check_counters
    print("INFO FUNCTION STARTED")
    user_id = ctx.author.id
    if len(args) == 0:
        await ctx.send("Please specify either 'true' or 'false' to enable or disable couch information notifications.")
    elif args[0] == "true":
        info_enabled[user_id] = True
        await ctx.send("Couch information notifications are now enabled!")
    elif args[0] == "false":
        info_enabled[user_id] = False
        await ctx.send("Couch information notifications are now disabled!.")
    else:
        await ctx.send("Please specify either 'true' or 'false' to enable or disable couch information notifications.")
        return

    while True:
        if not info_enabled.get(user_id):
            print("Info true not on")
            break

        global updates
        print(user_channels)
        print(updates)
        for user_id, channel_id in user_channels.items():
            user_id = str(user_id)
            if user_id in updates:
                # Process updates
                # ...

                # Reset the counter variable since an update was found
                user_check_counters[user_id] = 0
            else:
                # Increment the counter variable
                user_check_counters[user_id] += 1

            # Send the "No new couches were found" message every 15 checks
            if user_check_counters[user_id] == 60:
                if not user_updates.get(user_id):
                    user = await client.fetch_user(user_id)
                    channel = await client.fetch_channel(channel_id)
                    await channel.send("No new couches were found")

                # Reset the list of updates for the user
                user_updates[user_id] = []

                # Reset the counter variable
                user_check_counters[user_id] = 0

        # Wait for 10 seconds before checking again
        await asyncio.sleep(10)
            
        

    

last_stop_time = {}

@client.command()
async def phone(ctx, *args):
    if len(args) == 0:
        await ctx.send("Please specify either 'true' or 'false' to enable or disable text notifications.")
    elif args[0].lower() == 'true':
        await ctx.send("Please enter the phone number where you would like to receive text notifications.")
        try:
            phone_number = await client.wait_for('message', check=lambda m: m.author == ctx.author, timeout=30.0)
            # Store the phone number for the user
            user_id = str(ctx.author.id)
            phone_numbers[user_id] = phone_number.content
            await ctx.send(f"Text notifications enabled for {phone_number.content}.")
        except asyncio.TimeoutError:
            await ctx.send("Timed out. Please try again.")
    elif args[0].lower() == 'false':
        # Remove the phone number for the user
        user_id = str(ctx.author.id)
        del phone_numbers[user_id]
        await ctx.send("Text notifications disabled.")
    else:
        await ctx.send("Invalid input. Please specify either 'true' or 'false' to enable or disable text notifications.")

@client.command()
async def stop(ctx):
    global info_enabled

    # Check if 5 minutes have passed since the user last used !stop
    user_id = str(ctx.author.id)
    if user_id in stop_flags and time.time() - stop_flags[user_id] < 300:
        await ctx.send('You cannot use !stop again so soon')
        return

    # Update the last stop time for the user
    stop_flags[user_id] = time.time()

    # Stop the flipper for the user
    stoppers[user_id] = True
    await ctx.send('Stopping the flipper')

    # Set the info status to False for the specific user
    info_enabled[user_id] = False


@client.command()
async def max_price(ctx, price: int):
    user_id = str(ctx.author.id)
    if user_id in client_settings:
        client_settings[user_id]['max_price'] = price

        # Update the client_settings.csv file
        with open('client_settings.csv', 'w', newline='') as csvfile:
            fieldnames = ['user_id', 'email', 'password', 'max_price', 'location', 'range_couch']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for user_id, settings in client_settings.items():
                writer.writerow({'user_id': user_id, 'email': settings['email'], 'password': settings['password'], 'max_price': settings['max_price'], 'location': settings['location'], 'range_couch': settings['range_couch']})

        await ctx.send(f'Max price changed to {price}')
    else:
        await ctx.send('User settings not found. Please run the !start command to set up your settings first.')
        
        
@client.command()
async def update_email_password(ctx):
    user_id = str(ctx.author.id)
    if user_id in client_settings:
        # Prompt the user for the new email and password
        await ctx.send('Please enter your new Facebook email / phone number:')
        email_message = await client.wait_for('message', check=lambda message: message.author == ctx.author and not message.content.startswith('!'))
        new_email = email_message.content
        await email_message.delete()

        await ctx.send('Please enter your new Facebook password:')
        password_message = await client.wait_for('message', check=lambda message: message.author == ctx.author and not message.content.startswith('!'))
        new_password = password_message.content
        await password_message.delete()

        # Update the email and password in the client_settings dictionary
        client_settings[user_id]['email'] = new_email
        client_settings[user_id]['password'] = new_password

        # Update the client_settings.csv file
        with open('client_settings.csv', 'w', newline='') as csvfile:
            fieldnames = ['user_id', 'email', 'password', 'max_price', 'location', 'range_couch']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for user_id, settings in client_settings.items():
                writer.writerow({'user_id': user_id, 'email': settings['email'], 'password': settings['password'], 'max_price': settings['max_price'], 'location': settings['location'], 'range_couch': settings['range_couch']})

        await ctx.send('Email and password updated successfully.')
    else:
        await ctx.send('User settings not found. Please run the !start command to set up your settings first.')


@client.command()
async def update_location(ctx, *, location: str):
    user_id = str(ctx.author.id)
    if user_id in client_settings:
        client_settings[user_id]['location'] = location

        # Update the client_settings.csv file
        with open('client_settings.csv', 'w', newline='') as csvfile:
            fieldnames = ['user_id', 'email', 'password', 'max_price', 'location', 'range_couch']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for user_id, settings in client_settings.items():
                writer.writerow({'user_id': user_id, 'email': settings['email'], 'password': settings['password'], 'max_price': settings['max_price'], 'location': settings['location'], 'range_couch': settings['range_couch']})

        await ctx.send(f'Location changed to {location}')
    else:
        await ctx.send('User settings not found. Please run the !start command to set up your settings first.')
    

@client.command()
async def update_range(ctx, range_couch: int):
    user_id = str(ctx.author.id)
    if user_id in client_settings:
        client_settings[user_id]['range_couch'] = range_couch

        # Update the client_settings.csv file
        with open('client_settings.csv', 'w', newline='') as csvfile:
            fieldnames = ['user_id', 'email', 'password', 'max_price', 'location', 'range_couch']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for user_id, settings in client_settings.items():
                writer.writerow({'user_id': user_id, 'email': settings['email'], 'password': settings['password'], 'max_price': settings['max_price'], 'location': settings['location'], 'range_couch': settings['range_couch']})

        await ctx.send(f'Range changed to {range_couch} miles')
    else:
        await ctx.send('User settings not found. Please run the !start command to set up your settings first.')

client.run('MTA3NTgzNzE3NjUwMTI0Mzk1Ng.GLbED1.rrDNJEYOjZL90LJWF83oMOI7jDYt6k2i-FHerQ')