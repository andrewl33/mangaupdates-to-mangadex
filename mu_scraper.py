from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import yaml

credentials = {}
with open('credentials.yaml') as f:
    credentials = yaml.load(f)

url = 'https://www.mangaupdates.com/mylist.html'

# set driver options
options = webdriver.chrome.options.Options()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
driver = webdriver.Chrome(options=options)
driver.get(url)

# authenticate
username = driver.find_element_by_xpath("//input[@name='username']")
password = driver.find_element_by_xpath("//input[@name='password']")
submit = driver.find_element_by_xpath("//input[@src='images/login.gif']")

username.send_keys(credentials['username'])
password.send_keys(credentials['password'])
submit.click()

# wait for browser to refresh
time.sleep(1)

# access document
soup = BeautifulSoup(driver.page_source, 'html.parser')

# parse urls and titles
reading_list = soup.find("table", {"id": "list_table"})
title_url_list = reading_list.find_all("a", {"title": "Series Info"})
href_list = [a.get("href") for a in title_url_list]
title_list = [u.get_text() for u in title_url_list]

# exit selenium
driver.quit()
