from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import yaml


'''
mu_username: <account name>
mu_password: <password>
md_username:<account name>
md_password: <password>
'''
credentials = {}
with open('credentials.yaml') as f:
    credentials = yaml.load(f)

mu_url = 'https://www.mangaupdates.com/mylist.html'
md_login_url = 'https://mangadex.org/login'
md_search_url = 'https://mangadex.org/quick_search/'

# set driver options
options = webdriver.chrome.options.Options()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
driver = webdriver.Chrome(options=options)
driver.get(mu_url)

# authenticate
username = driver.find_element_by_xpath("//input[@name='username']")
password = driver.find_element_by_xpath("//input[@name='password']")
submit = driver.find_element_by_xpath("//input[@src='images/login.gif']")

username.send_keys(credentials['mu_username'])
password.send_keys(credentials['mu_password'])
submit.click()

# access document
soup = BeautifulSoup(driver.page_source, 'html.parser')

# parse urls and titles
reading_list = soup.find("table", {"id": "list_table"})
title_url_list = reading_list.find_all("a", {"title": "Series Info"})
href_list = [a.get("href") for a in title_url_list]
title_list = [u.get_text() for u in title_url_list]

# get all titles
all_titles = {}

# initially fill with known values
for i in range(len(title_list)):
    new_set = set()
    new_set.add(title_list[i])
    all_titles[href_list[i]] = new_set


# scrape each individual page
for manga_urls in href_list:
    driver.get(manga_urls)

    # alternate titles are under first sContainer, third sContent
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    title_html = soup.find_all("div", {"class": "sContent"})[3]
    title_list = title_html.find_all(text=True)
    title_list = [title.strip(' \t\n\r')
                  for title in title_list if title != '\n']
    all_titles[manga_urls].update(title_list)

# login to mangadex
driver.get(md_login_url)
username = driver.find_element_by_id("login_username")
password = driver.find_element_by_id("login_password")
submit = driver.find_element_by_id("login_button")

username.send_keys(credentials['md_username'])
password.send_keys(credentials['md_password'])
submit.click()

# mangadex can be slow sometimes
time.sleep(2)


def is_english(s):
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True


# start searching
for titles in all_titles.values():
    for title_name in titles:
        if not is_english(title_name):
            continue
        query = title_name.replace(" ", "%20")
        driver.get(md_search_url+query)
        try:
            manga_entries = driver.find_elements_by_class_name("manga-entry")
            if manga_entries:
                try:
                    time.sleep(2)  # wait for jQuery to load
                    follow_btn = manga_entries[0].find_elements_by_xpath(
                        "//button[contains(@class, 'manga_follow_button') and contains(@id, '1')]")
                    follow_btn[0].click()
                    time.sleep(1)
                except:
                    print(title_name, "already followed")
                    pass
                break
        except:
            pass
        time.sleep(2)
# exit selenium
driver.quit()
