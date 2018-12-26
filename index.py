'''
imports reading list from mangaupdates.com to mangadex.org

requires:
beautifulsoup4
chromedriver-binary (to be installed in python3 directory)
PyYAML
selenium

./credentials.yaml

mu_username: <account name>
mu_password: <password>
md_username:<account name>
md_password: <password>
'''
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import yaml


# constants
# delays
MANGA_UPDATES_DELAY = 0  # seconds for manga updates to load, usually can be set to 0
MANGADEX_DELAY = 2  # seconds for mangadex to load (jQuery takes forever)

# urls
mu_url = 'https://www.mangaupdates.com/mylist.html'
mu_url_wish_list = 'https://www.mangaupdates.com/mylist.html?list=wish'
mu_url_complete_list = 'https://www.mangaupdates.com/mylist.html?list=complete'
mu_url_unfinished_list = 'https://www.mangaupdates.com/mylist.html?list=unfinished'
mu_url_on_hold_list = 'https://www.mangaupdates.com/mylist.html?list=hold'
md_login_url = 'https://mangadex.org/login'
md_search_url = 'https://mangadex.org/quick_search/'


def manga_updates_all_titles(href_list, title_list, driver):
    '''
    get a list of titles and returns a dict of manga_updates_url: set(all titles)
    '''
    all_titles = {}

    # initially fill with known values
    for i in range(len(title_list)):
        new_set = set()
        new_set.add(title_list[i])
        all_titles[href_list[i]] = new_set

    # scrape each individual page for alternative titles
    for manga_urls in href_list:
        driver.get(manga_urls)
        time.sleep(MANGA_UPDATES_DELAY)

        # alternate titles are under first sContainer, third sContent
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        title_html = soup.find_all("div", {"class": "sContent"})[3]
        title_list = title_html.find_all(text=True)
        title_list = [title.strip(' \t\n\r')
                      for title in title_list if title != '\n']
        all_titles[manga_urls].update(title_list)

        return all_titles


def is_english(s):
    '''
    tests to see if the characters are english
    MangaDex does not have non-english characters titles
    '''
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True


def mangadex_import(all_titles, driver, type="reading"):
    '''
    imports to correct list base on an all_titles dict
    all_titles: manga_updates_url: set(titles)
    '''

    x_path_string = ""

    if type == "reading":
        x_path_string = "//button[contains(@class, 'manga_follow_button') and contains(@id, '1')]"
    elif type == "completed":
        x_path_string = "//a[contains(@class, 'manga_follow_button') and contains(@id, '2')]"
    elif type == "on hold":
        x_path_string = "//button[contains(@class, 'manga_follow_button') and contains(@id, '3')]"
    elif type == "plan to read":
        x_path_string = "//button[contains(@class, 'manga_follow_button') and contains(@id, '4')]"
    elif type == "dropped":
        x_path_string = "//button[contains(@class, 'manga_follow_button') and contains(@id, '5')]"
    else:
        raise Exception(
            "import type should be: 'reading', 'completed', 'on hold', 'plan to read', 'dropped'")

    # start searching
    for titles in all_titles.values():
        for title_name in titles:
            if not is_english(title_name):
                continue
            query = title_name.replace(" ", "%20")
            driver.get(md_search_url+query)
            time.sleep(MANGADEX_DELAY)

            try:
                manga_entries = driver.find_elements_by_class_name(
                    "manga-entry")
                if manga_entries:
                    try:
                        time.sleep(MANGADEX_DELAY)  # wait for jQuery to load
                        follow_btn = manga_entries[0].find_elements_by_xpath(
                            x_path_string)
                        follow_btn[0].click()
                    except:
                        print(title_name, "already imported")
                        pass
                    break
            except:
                pass


def main():
    # get credentials
    credentials = {}
    with open('credentials.yaml') as f:
        credentials = yaml.load(f)

    # set driver options
    options = webdriver.chrome.options.Options()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    driver = webdriver.Chrome(options=options)
    driver.get(mu_url)
    time.sleep(MANGA_UPDATES_DELAY)

    # authenticate
    username = driver.find_element_by_xpath("//input[@name='username']")
    password = driver.find_element_by_xpath("//input[@name='password']")
    submit = driver.find_element_by_xpath("//input[@src='images/login.gif']")

    username.send_keys(credentials['mu_username'])
    password.send_keys(credentials['mu_password'])
    submit.click()
    time.sleep(MANGA_UPDATES_DELAY)

    # access document
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # parse urls and titles of reading list
    reading_list = soup.find("table", {"id": "list_table"})
    title_url_list = reading_list.find_all("a", {"title": "Series Info"})
    href_list = [a.get("href") for a in title_url_list]
    title_list = [u.get_text() for u in title_url_list]

    all_reading_list = manga_updates_all_titles(href_list, title_list, driver)

    # login to mangadex
    driver.get(md_login_url)
    time.sleep(MANGADEX_DELAY)

    username = driver.find_element_by_id("login_username")
    password = driver.find_element_by_id("login_password")
    submit = driver.find_element_by_id("login_button")

    username.send_keys(credentials['md_username'])
    password.send_keys(credentials['md_password'])
    submit.click()

    # mangadex can be slow sometimes
    time.sleep(MANGADEX_DELAY)

    # import by type
    mangadex_import(all_reading_list, driver)

    # exit selenium
    driver.quit()


if __name__ == "__main__":
    main()
